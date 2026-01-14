import json
import os
import math
import re

STATE_FILE = "state.json"
README_FILE = "README.md"

def load_state():
    if not os.path.exists(STATE_FILE):
        # Default starting shape
        return {
            "top":    [0.0,  0.0,  15.0],
            "bottom": [0.0,  0.0, -15.0],
            "waist_1": [10.0, 0.0,  0.0],
            "waist_2": [0.0,  10.0, 0.0],
            "waist_3": [-10.0, 0.0, 0.0],
            "waist_4": [0.0, -10.0, 0.0]
        }
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def parse_issue_body():
    body = os.environ.get("ISSUE_BODY", "")
    lines = body.split('\n')
    
    vertex_name = None
    axis_name = None
    amount = 0.0
    
    for i, line in enumerate(lines):
        if line.strip() == "### Which point do you want to move?":
            vertex_name = lines[i+2].strip()
        elif line.strip() == "### Which direction?":
            axis_name = lines[i+2].strip()
        elif line.strip() == "### Amount to move (Positive or Negative)":
            try:
                amount = float(lines[i+2].strip())
            except ValueError:
                amount = 0.0
                
    return vertex_name, axis_name, amount

def generate_stl_string(state):
    # Unpack vertices
    t = state["top"]
    b = state["bottom"]
    w1 = state["waist_1"]
    w2 = state["waist_2"]
    w3 = state["waist_3"]
    w4 = state["waist_4"]

    stl_content = ["solid sculpted_mesh"]

    def add_facet(v1, v2, v3):
        # Calc Normal
        ux, uy, uz = v2[0]-v1[0], v2[1]-v1[1], v2[2]-v1[2]
        vx, vy, vz = v3[0]-v1[0], v3[1]-v1[1], v3[2]-v1[2]
        nx, ny, nz = uy*vz - uz*vy, uz*vx - ux*vz, ux*vy - uy*vx
        l = math.sqrt(nx*nx + ny*ny + nz*nz)
        if l == 0: l = 1
        
        stl_content.append(f"  facet normal {nx/l:.4f} {ny/l:.4f} {nz/l:.4f}")
        stl_content.append("    outer loop")
        for v in [v1, v2, v3]:
            stl_content.append(f"      vertex {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}")
        stl_content.append("    endloop")
        stl_content.append("  endfacet")

    # Top faces
    add_facet(t, w1, w2)
    add_facet(t, w2, w3)
    add_facet(t, w3, w4)
    add_facet(t, w4, w1)
    # Bottom faces
    add_facet(b, w2, w1)
    add_facet(b, w3, w2)
    add_facet(b, w4, w3)
    add_facet(b, w1, w4)

    stl_content.append("endsolid")
    return "\n".join(stl_content)

def update_readme(new_stl):
    with open(README_FILE, "r") as f:
        content = f.read()

    # Regex to replace content between markers
    # We use DOTALL so . matches newlines
    pattern = r"()(.*?)()"
    replacement = f"\\1\n{new_stl}\n\\3"
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(README_FILE, "w") as f:
        f.write(new_content)

if __name__ == "__main__":
    state = load_state()
    
    # Update State if running from Issue
    if "ISSUE_BODY" in os.environ:
        v_name, axis_str, amount = parse_issue_body()
        
        axis_idx = 0
        if "Y" in axis_str: axis_idx = 1
        if "Z" in axis_str: axis_idx = 2
        
        if v_name in state:
            state[v_name][axis_idx] += amount
            
            with open(STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)

    # Generate STL String and Inject into README
    stl_data = generate_stl_string(state)
    update_readme(stl_data)
