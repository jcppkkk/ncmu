from textual.dom import DOMNode

new_css = []
find_cursor = False
removed_color = False
for line in DOMNode.DEFAULT_CSS.split("\n"):
    if not removed_color:
        if find_cursor:
            if "color: $block-cursor-foreground;" in line:
                removed_color = True
                continue
        elif "& > .datatable--cursor {" in line:
            find_cursor = True
    new_css.append(line)

DOMNode.DEFAULT_CSS = "\n".join(new_css)
