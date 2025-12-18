import os

def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt from the prompts directory, path relative to this file.
    
    Args:
        prompt_name: Name of the prompt file (without .md extension)
        
    Returns:
        The prompt content as a string
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_dir = os.path.join(current_dir, '../prompts')
    prompt_path = os.path.join(prompts_dir, f'{prompt_name}.md')
    
    with open(prompt_path, 'r') as f:
        return f.read()
