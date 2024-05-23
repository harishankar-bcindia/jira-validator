# class Logger:
#     def __init__(self, verbose_level=0):
#         verbose_level = (
#             2 if isinstance(verbose_level, bool) and verbose_level else verbose_level
#         )
#         self.verbose_level = verbose_level

#     def log(self, level, message):
#         level_map = {"debug": 1, "info": 2}
#         if self.verbose_level and level_map.get(level, 0) <= self.verbose_level:
#             print(f"[{level.upper()}]: {message}")


import logging
import os
 
class Logger:
    def __init__(self, verbose_level=0, log_folder='logs', log_filename='example.json'):
        verbose_level = 2 if isinstance(verbose_level, bool) and verbose_level else verbose_level
        self.verbose_level = verbose_level
 
        # Create a 'logs' folder if it doesn't exist
        os.makedirs(log_folder, exist_ok=True)
 
        # Configure logging to both console and file
        log_file_path = os.path.join(log_folder, log_filename)
        logging.basicConfig(
            filename=log_file_path,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
    def log(self, level, message):
        level_map = {"debug": 1, "info": 2}
        if self.verbose_level and level_map.get(level, 0) <= self.verbose_level:
            print(f"\n[{level.upper()}]: {message}")
            logging.log(logging.DEBUG if level == 'debug' else logging.INFO, message)
 
 
 
# # Example usage
# if __name__ == "__main__":
#     # Initialize Logger with log_folder and log_filename specified
#     logger = Logger(verbose_level=2, log_folder='logs', log_filename='example.log')
 
#     # Log messages
#     logger.log('debug', 'This is a debug message')
#     logger.log('info', 'This is an info message')