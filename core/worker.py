import os
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal


class ProcessWorker(QThread):
    """Worker thread for processing PDFs asynchronously"""
    progress_updated = pyqtSignal(str, int, int)  # process_id, current, total
    status_changed = pyqtSignal(str, str)  # process_id, status
    finished = pyqtSignal(str, bool, str)  # process_id, success, message
    log_message = pyqtSignal(str, str)  # process_id, message

    def __init__(self, process_data, settings):
        super().__init__()
        self.process_data = process_data
        self.settings = settings
        self.is_paused = False
        self.is_cancelled = False

    def run(self):
        """Execute the PDF processing"""
        process_id = self.process_data['id']
        instruction = self.process_data['instruction']
        pdf_folder = self.process_data['pdf_folder']
        output_folder = self.process_data['output_folder']
        model_name = self.process_data.get('model_name', 'ServiceNow-AI/Apriel-1.6-15b-Thinker:together')

        try:
            self.log_message.emit(process_id, "Initializing process...")

            # Import here to avoid issues with threading
            from openai import OpenAI
            from utils.pdf_extract import extract_text_with_precision

            # Initialize OpenAI client
            api_key = self.settings.get('hf_api_key', '')
            if not api_key:
                self.finished.emit(process_id, False, "API key not configured")
                return

            client = OpenAI(
                base_url="https://router.huggingface.co/v1",
                api_key=api_key,
            )

            # Get all PDF files
            if not os.path.exists(pdf_folder):
                self.finished.emit(process_id, False, "PDF folder does not exist")
                return

            pdf_files = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]
            total_files = len(pdf_files)

            if total_files == 0:
                self.finished.emit(process_id, False, "No PDF files found in folder")
                return

            self.log_message.emit(process_id, f"Found {total_files} PDF files")
            self.log_message.emit(process_id, f"Using model: {model_name}")
            self.status_changed.emit(process_id, "running")

            # Create output folder if it doesn't exist
            os.makedirs(output_folder, exist_ok=True)

            # Update total first
            self.progress_updated.emit(process_id, 0, total_files)

            # Process each PDF
            successful_count = 0
            failed_count = 0

            for idx, pdf_file in enumerate(pdf_files):
                if self.is_cancelled:
                    self.status_changed.emit(process_id, "cancelled")
                    self.finished.emit(process_id, False, "Process cancelled by user")
                    return

                # Handle pause
                while self.is_paused and not self.is_cancelled:
                    self.msleep(100)

                if self.is_cancelled:
                    self.status_changed.emit(process_id, "cancelled")
                    self.finished.emit(process_id, False, "Process cancelled by user")
                    return

                try:
                    self.log_message.emit(process_id, f"Processing: {pdf_file}")

                    # Extract text from PDF
                    pdf_path = os.path.join(pdf_folder, pdf_file)

                    # Try to extract with error handling for corrupted PDFs
                    try:
                        content = extract_text_with_precision(pdf_path)
                    except Exception as pdf_error:
                        self.log_message.emit(process_id, f"PDF Error in {pdf_file}: {str(pdf_error)}")
                        self.log_message.emit(process_id, f"Skipping corrupted/invalid PDF: {pdf_file}")
                        failed_count += 1
                        # Update progress even for skipped files
                        self.progress_updated.emit(process_id, idx + 1, total_files)
                        continue

                    if not content or len(content.strip()) == 0:
                        self.log_message.emit(process_id, f"Warning: No text extracted from {pdf_file}")
                        failed_count += 1
                        # Update progress even for empty files
                        self.progress_updated.emit(process_id, idx + 1, total_files)
                        continue

                    # Call API with specified model
                    completion = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": instruction},
                            {"role": "user", "content": content}
                        ],
                        max_tokens = 72000,
                        extra_body={
                            "reasoning" : {
                                "effort" : "high"
                            }
                        },
                    )

                    # Save result
                    result_filename = f"{idx + 1:03d}_{Path(pdf_file).stem}.md"
                    result_path = os.path.join(output_folder, result_filename)

                    with open(result_path, 'w', encoding='utf-8') as f:
                        f.write(completion.choices[0].message.content)

                    successful_count += 1
                    self.log_message.emit(process_id, f"✓ Completed: {pdf_file}")

                except Exception as e:
                    failed_count += 1
                    self.log_message.emit(process_id, f"✗ Error processing {pdf_file}: {str(e)}")

                # Always update progress after each file (success or failure)
                self.progress_updated.emit(process_id, idx + 1, total_files)

                # Small delay to ensure UI updates
                self.msleep(50)

            self.status_changed.emit(process_id, "completed")
            summary = f"Finished: {successful_count} successful, {failed_count} failed/skipped out of {total_files} files"
            self.finished.emit(process_id, True, summary)

        except Exception as e:
            self.status_changed.emit(process_id, "failed")
            self.finished.emit(process_id, False, f"Error: {str(e)}")

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def cancel(self):
        self.is_cancelled = True
