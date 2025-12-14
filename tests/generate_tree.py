import os

def generate_tree(path, prefix=""):
    entries = sorted(os.listdir(path))
    tree_str = ""

    for index, entry in enumerate(entries):
        full_path = os.path.join(path, entry)
        connector = "├── " if index < len(entries) - 1 else "└── "

        tree_str += prefix + connector + entry + "\n"

        if os.path.isdir(full_path):
            extension = "│   " if index < len(entries) - 1 else "    "
            tree_str += generate_tree(full_path, prefix + extension)

    return tree_str


if __name__ == "__main__":
    root = "src"
    tree_text = generate_tree(root)

    print(tree_text)

    with open("docs/raw_directory_tree.txt", "w", encoding="utf-8") as f:
        f.write(tree_text)
