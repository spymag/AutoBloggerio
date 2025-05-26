import markdown2

markdown_string = "# This is an H1 Title"
html_output = markdown2.markdown(markdown_string, extras=["fenced-code-blocks", "cuddled-lists", "tables"])

print("---MARKDOWN INPUT---")
print(markdown_string)
print("---HTML OUTPUT---")
print(html_output)

markdown_string_h2 = "## This is an H2 Title"
html_output_h2 = markdown2.markdown(markdown_string_h2, extras=["fenced-code-blocks", "cuddled-lists", "tables"])
print("---MARKDOWN INPUT (H2)---")
print(markdown_string_h2)
print("---HTML OUTPUT (H2)---")
print(html_output_h2)
