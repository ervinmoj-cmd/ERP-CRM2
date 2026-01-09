with open('templates/formulario.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the start of the script block to remove
start_marker = '<!-- Auto-populate clients and cascading equipment filters -->'
end_marker = '// ============ LOAD DRAFT DATA IF IN EDIT MODE ============'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    # Keep the start marker and the end marker, but replace the content in between
    # Actually, we want to keep the <script> tag opening if it's outside?
    # No, the start marker is before the <script>.
    # Let's replace the whole block with a comment pointing to the new file.
    
    new_content = content[:start_idx] + '''<!-- Auto-populate clients and cascading equipment filters -->
  <script>
    // Logic moved to static/js/cliente_autofill.js
    document.addEventListener('DOMContentLoaded', function () {
       
       ''' + content[end_idx:]
    
    with open('templates/formulario.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully removed conflicting script.")
else:
    print("Could not find markers.")
    print(f"Start found: {start_idx}")
    print(f"End found: {end_idx}")
