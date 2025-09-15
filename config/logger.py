import logging
import sys
import traceback
import json
from datetime import datetime
from typing import Any, Dict, Optional
from colorama import init, Fore, Style, Back
import functools
import inspect
import os

# Initialize colorama for colored output
init()

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.MAGENTA + Style.BRIGHT,
    }
    
    def format(self, record):
        # Add color to the log level
        level_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{level_color}{record.levelname}{Style.RESET_ALL}"
        
        # Format the message
        formatted = super().format(record)
        return formatted

class RequestTracer:
    """Traces the complete request flow with detailed logging"""
    
    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode
        self.request_id = None
        self.flow_stack = []
        self.start_time = None
        
    def set_debug_mode(self, debug_mode: bool):
        """Set debug mode on/off"""
        self.debug_mode = debug_mode
        
    def start_request(self, user_input: str) -> str:
        """Start tracing a new request"""
        self.request_id = f"REQ_{datetime.now().strftime('%H%M%S_%f')}"
        self.start_time = datetime.now()
        self.flow_stack = []
        
        if self.debug_mode:
            print(f"\n{Back.BLUE}{Fore.WHITE}{'='*80}{Style.RESET_ALL}")
            print(f"{Back.BLUE}{Fore.WHITE} 🚀 NEW REQUEST STARTED - ID: {self.request_id} {Style.RESET_ALL}")
            print(f"{Back.BLUE}{Fore.WHITE}{'='*80}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📝 USER INPUT: {Fore.WHITE}{user_input}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}⏰ TIMESTAMP: {Fore.WHITE}{self.start_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}{Style.RESET_ALL}")
        else:
            # Production mode - simple input display
            print(f"\n{Fore.CYAN}📝 USER: {Fore.WHITE}{user_input}{Style.RESET_ALL}")
        
        return self.request_id
    
    def log_function_entry(self, func_name: str, file_path: str, inputs: Dict[str, Any] = None):
        """Log when entering a function"""
        if not self.debug_mode:
            return
            
        self.flow_stack.append(func_name)
        depth = len(self.flow_stack)
        indent = "  " * depth
        
        print(f"\n{Fore.BLUE}{'→' * depth} ENTERING: {Fore.YELLOW}{func_name}{Style.RESET_ALL}")
        print(f"{indent}{Fore.BLUE}📁 FILE: {Fore.WHITE}{file_path}{Style.RESET_ALL}")
        
        if inputs:
            print(f"{indent}{Fore.BLUE}📥 INPUTS:{Style.RESET_ALL}")
            for key, value in inputs.items():
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value, indent=2, default=str)[:200]
                    if len(str(value)) > 200:
                        value_str += "..."
                else:
                    value_str = str(value)[:200]
                print(f"{indent}  {Fore.CYAN}{key}: {Fore.WHITE}{value_str}{Style.RESET_ALL}")
    
    def log_function_exit(self, func_name: str, outputs: Any = None, execution_time: float = None):
        """Log when exiting a function"""
        if not self.debug_mode:
            return
            
        if self.flow_stack and self.flow_stack[-1] == func_name:
            self.flow_stack.pop()
        
        depth = len(self.flow_stack) + 1
        indent = "  " * depth
        
        print(f"{Fore.GREEN}{'←' * depth} EXITING: {Fore.YELLOW}{func_name}{Style.RESET_ALL}")
        
        if execution_time:
            print(f"{indent}{Fore.GREEN}⏱️  EXECUTION TIME: {Fore.WHITE}{execution_time:.3f}s{Style.RESET_ALL}")
        
        if outputs is not None:
            print(f"{indent}{Fore.GREEN}📤 OUTPUTS:{Style.RESET_ALL}")
            if isinstance(outputs, (dict, list)):
                output_str = json.dumps(outputs, indent=2, default=str)[:300]
                if len(str(outputs)) > 300:
                    output_str += "..."
            else:
                output_str = str(outputs)[:300]
            print(f"{indent}  {Fore.WHITE}{output_str}{Style.RESET_ALL}")
    
    def log_api_call(self, api_name: str, method: str, params: Dict[str, Any] = None, response: Any = None):
        """Log external API calls"""
        if not self.debug_mode:
            return
            
        depth = len(self.flow_stack) + 1
        indent = "  " * depth
        
        print(f"\n{indent}{Fore.MAGENTA}🌐 API CALL: {Fore.YELLOW}{api_name}.{method}{Style.RESET_ALL}")
        
        if params:
            print(f"{indent}{Fore.MAGENTA}📋 PARAMETERS:{Style.RESET_ALL}")
            for key, value in params.items():
                print(f"{indent}  {Fore.CYAN}{key}: {Fore.WHITE}{str(value)[:100]}{Style.RESET_ALL}")
        
        if response is not None:
            print(f"{indent}{Fore.MAGENTA}📨 RESPONSE:{Style.RESET_ALL}")
            if isinstance(response, (dict, list)):
                response_str = json.dumps(response, indent=2, default=str)[:200]
                if len(str(response)) > 200:
                    response_str += "..."
            else:
                response_str = str(response)[:200]
            print(f"{indent}  {Fore.WHITE}{response_str}{Style.RESET_ALL}")
    
    def log_error(self, error: Exception, context: str = ""):
        """Log errors with context"""
        depth = len(self.flow_stack) + 1 if self.debug_mode else 0
        indent = "  " * depth
        
        print(f"\n{indent}{Fore.RED}❌ ERROR in {context}:{Style.RESET_ALL}")
        print(f"{indent}  {Fore.RED}Type: {Fore.WHITE}{type(error).__name__}{Style.RESET_ALL}")
        print(f"{indent}  {Fore.RED}Message: {Fore.WHITE}{str(error)}{Style.RESET_ALL}")
        
        if self.debug_mode:
            # Print traceback only in debug mode
            tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
            print(f"{indent}  {Fore.RED}Traceback:{Style.RESET_ALL}")
            for line in tb_lines[-3:]:  # Show last 3 lines of traceback
                print(f"{indent}    {Fore.RED}{line.strip()}{Style.RESET_ALL}")
    
    def end_request(self, final_response: str):
        """End request tracing"""
        end_time = datetime.now()
        total_time = (end_time - self.start_time).total_seconds()
        
        if self.debug_mode:
            print(f"\n{Back.GREEN}{Fore.WHITE}{'='*80}{Style.RESET_ALL}")
            print(f"{Back.GREEN}{Fore.WHITE} 🏁 REQUEST COMPLETED - ID: {self.request_id} {Style.RESET_ALL}")
            print(f"{Back.GREEN}{Fore.WHITE}{'='*80}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}🎯 FINAL RESPONSE: {Fore.WHITE}{final_response[:200]}{'...' if len(final_response) > 200 else ''}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}⏰ TOTAL TIME: {Fore.WHITE}{total_time:.3f}s{Style.RESET_ALL}")
            print(f"{Fore.GREEN}📊 FUNCTIONS CALLED: {Fore.WHITE}{len(self.flow_stack) if self.flow_stack else 'All completed'}{Style.RESET_ALL}")
            print(f"{Back.GREEN}{Fore.WHITE}{'='*80}{Style.RESET_ALL}\n")
        else:
            # Production mode - simple output display
            print(f"{Fore.GREEN}🤖 BOT: {Fore.WHITE}{final_response}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}⏰ Response time: {Fore.WHITE}{total_time:.3f}s{Style.RESET_ALL}\n")

# Initialize request tracer with debug mode from config
from config.settings import Config
request_tracer = RequestTracer(debug_mode=Config.DEBUG_MODE)

def setup_logging():
    """Setup logging configuration"""
    # Create logger
    logger = logging.getLogger('meeting_scheduler')
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler with colored formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger

def trace_function(func):
    """Decorator to trace function calls"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get function info
        func_name = func.__name__
        file_path = inspect.getfile(func)
        relative_path = os.path.relpath(file_path)
        
        # Prepare inputs for logging
        inputs = {}
        if args:
            inputs['args'] = args
        if kwargs:
            inputs['kwargs'] = kwargs
        
        # Log function entry
        start_time = datetime.now()
        request_tracer.log_function_entry(func_name, relative_path, inputs)
        
        try:
            # Execute function
            result = func(*args, **kwargs)
            
            # Log function exit
            execution_time = (datetime.now() - start_time).total_seconds()
            request_tracer.log_function_exit(func_name, result, execution_time)
            
            return result
            
        except Exception as e:
            # Log error
            request_tracer.log_error(e, func_name)
            raise
    
    return wrapper

def trace_api_call(api_name: str, method: str):
    """Decorator to trace API calls"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Log API call
            params = {
                'args': args if args else None,
                'kwargs': kwargs if kwargs else None
            }
            
            try:
                result = func(*args, **kwargs)
                request_tracer.log_api_call(api_name, method, params, result)
                return result
            except Exception as e:
                request_tracer.log_api_call(api_name, method, params, f"ERROR: {str(e)}")
                raise
        
        return wrapper
    return decorator

# Initialize logger
logger = setup_logging() 