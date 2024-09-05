def dict_to_text_description(changes_dict):
    description = []
    for key, value in changes_dict.items():
        old_value = value['old']
        new_value = value['new']
        if old_value != new_value:
            description.append(f"The {key} was changed from '{old_value}' to '{new_value}'.")
        else:
            description.append(f"The {key} remained unchanged at '{old_value}'.")
    
    return " ".join(description)