import re

with open('src/nova/parser.py', 'r') as f:
    content = f.read()

# Remove , line=self.line from constructor calls
content = content.replace(', line=self.line', '')
# Handle cases like Node(line=self.line) -> Node()
content = re.sub(r'\(line=self.line\)', r'()', content)

# Instead, find where a node is returned and set the line attribute.
# This is tricky with nested expressions.
# A better way is to wrap node creation in a helper.

methods = re.split(r'(    def \w+\(self.*?\):)', content)
new_content = [methods[0]]
for i in range(1, len(methods), 2):
    header = methods[i]
    body = methods[i+1]

    # Simple replacement: return NodeClass(...) -> node = NodeClass(...); node.line = self.line; return node
    # But only for top-level returns in methods.

    body = re.sub(r'return (\w+)\((.*?)\)', r'__node = \1(\2); __node.line = self.line; return __node', body)

    new_content.append(header)
    new_content.append(body)

with open('src/nova/parser.py', 'w') as f:
    f.write("".join(new_content))
