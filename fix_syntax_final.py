
import os
import re

file_path = r'c:\Users\INAIR 005\OneDrive\Escritorio\PYTHON\p9\p6\inair_reportes\templates\admin_crm_view.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find the broken function start
# We look for "function guardarMensajeEmail() {" followed by potentially broken lines
# and replace the start of the function up to "const firma"
# likely broken content:
# function guardarMensajeEmail() {
#            const dealId = {{ deal.id }
#        };
#        const firma = ...

# We want to replace it with:
# function guardarMensajeEmail() {
#            const dealId = {{ deal.id }};
#            const firma = ...

# Let's try to match a wide chunk to be safe
start_marker = "function guardarMensajeEmail() {"
end_marker = "const firma = document.getElementById('firmaVendedor').value;"

pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL)

replacement = """function guardarMensajeEmail() {
            const dealId = {{ deal.id }};
            const firma = document.getElementById('firmaVendedor').value;"""

new_content, count = pattern.subn(replacement, content)

if count > 0:
    print(f"Fixed {count} occurrences of the broken function header.")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
else:
    print("Could not find the broken pattern using regex. Trying backup simple string replacement.")
    
    # Backup: Look for the specific broken Jinja line if regex failed (maybe extra spaces?)
    broken_line_part = "const dealId = {{ deal.id }"
    
    lines = content.split('\n')
    new_lines = []
    fixed = False
    skip_next = False
    
    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue
            
        if "const dealId = {{ deal.id }" in line and "}}" not in line:
            print(f"Found broken line at {i+1}: {line}")
            # Check if next line is simply "};" or similar
            if i + 1 < len(lines) and "};" in lines[i+1]:
                print(f"And found closing brace at {i+2}")
                new_lines.append("            const dealId = {{ deal.id }};")
                skip_next = True
                fixed = True
            else:
                 # Just fix this line and hope the next line isn't garbage
                 new_lines.append("            const dealId = {{ deal.id }};")
                 fixed = True
        else:
            new_lines.append(line)
            
    if fixed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        print("Fixed via line iteration.")
    else:
        print("No broken lines found. File might already be fixed or pattern is different.")

