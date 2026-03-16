from models.layouts_schema import Layout


def get_layout_schema_from_user(header: str, datarow: str, footer: str) -> str:
    """
    Interrupt logic to fetch layout schema from the user when no matching layout is found in the database.
    Returns the layout as a JSON string, or None if the user declines.
    """
    user_approval = input("No matching layout found for the provided file. Do you want to provide a layout schema? (yes/no): ").strip().lower()

    if user_approval not in ['yes', 'y']:
        return ""

    instructions = f"""
    Please provide a JSON schema text file path for the layout based on the following details:
    Header: {header}
    Data Row: {datarow}
    Footer: {footer}
    The JSON schema should follow this format:
    {{
    "table_name": "<table_name>",
    "columns": [
        {{
        "cid": <int>,
        "name": "<column_name>",
        "type": "<data_type>",
        "notnull": <true/false>,
        "is_primary_key": <true/false>,
        "default_value": <value or null>
        }}...
    ],
    "metadata": [
        {{
        "column_name": "<column_name>",
        "start_pos": <int or null>,
        "length": <int or null>,
        "validations": "<validation_rules or null>",
        "is_decimal": <true/false>,
        "decimal_pos": <int or null>
        }}...
    ]
    }}
    Your Input: 
    """

    print(instructions)
    while True:
        user_input = input("Provide the JSON schema text file path: ")

        try:
            with open(user_input, 'r') as file:
                json_content = file.read()
            layout = Layout.model_validate_json(json_content)
            should_save_layout = input("Do you want to save this layout for future use? (yes/no): ").strip().lower()
            if should_save_layout in ['yes', 'y']:
                # TODO: Logic to save the layout to the database can be implemented here
                print("Layout saved successfully.")
            return layout.model_dump_json()

        except Exception as e:
            print(f"Invalid input. Please ensure you provide a valid JSON schema that matches the required format. Error details: {str(e)}")
            return ""