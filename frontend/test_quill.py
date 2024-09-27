import streamlit as st

from streamlit_quill import st_quill

import markdownify

# Spawn a new Quill editor
content = st_quill(html=True, preserve_whitespace=True)

# Display editor's content as you type
content
n = content.count("\n")
print(markdownify.markdownify(content, heading_style="ATX"))