import os
from jinja2 import Template

def parse_html_from_template(template_name: str, template_data: dict) -> str:
    """
    Parses an HTML or XML template and dynamically replaces placeholders.
    
    :param template_name: The name of the template file (HTML/XML)
    :param template_data: A dictionary of data to fill in the template placeholders.
    :return: The parsed HTML content as a string.
    """
    # Define template directory
    template_dir = os.path.join(os.path.dirname(__file__), '../templates')
    
    # Construct the full path to the template
    template_path = os.path.join(template_dir, template_name)
    
    with open(template_path) as file_:
        template_content = file_.read()
    
    # Create a Jinja2 template and render it with data
    template = Template(template_content)
    return template.render(**template_data)
