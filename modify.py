import json
import os
import math

STATE_FILE = "state.json"
README_FILE = "README.md"
# TODO: Update this to your Cloudflare Pages URL after setup (e.g., "https://stl-generator.pages.dev/")
SITE_URL = "https://matissesprojects.github.io/STL-Generator/"

def load_state():
    if not os.path.exists(STATE_FILE):
        # NEW SHAPE: Octahedron (6 vertices)
        return {
            "top":    [0.0,   0.0,  12.0],
            "bottom": [0.0,   0.0, -12.0],
            "front":  [10.0,  0.0,  0.0],
            "back":   [-10.0, 0.0,  0.0],
            "left":   [0.0,   10.0, 0.0],
            "right":  [0.0,  -10.0, 0.0]
        }
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def parse_issue_body():
    body = os.environ.get("ISSUE_BODY", "")
    lines = body.split('\n')
    
    vertex_name = ''
    axis_name = ''
    amount = 0.0
    
    for i, line in enumerate(lines):
        if line.strip() == "### Which point do you want to move?":
            vertex_name = lines[i+2].strip().lower()
        elif line.strip() == "### Which direction?":
            axis_name = lines[i+2].strip()
        elif line.strip() == "### Amount to move (Positive or Negative)":
            try:
                amount = float(lines[i+2].strip())
            except ValueError:
                amount = 0.0
                
    return vertex_name, axis_name, amount

def generate_stl_content(state):
    # Unpack 6 vertices
    t = state["top"]
    b = state["bottom"]
    f_pt = state["front"]
    bk = state["back"]
    l = state["left"]
    r = state["right"]

    lines = ["solid collaborative_crystal"]

    def add_facet(v1, v2, v3):
        ux, uy, uz = v2[0]-v1[0], v2[1]-v1[1], v2[2]-v1[2]
        vx, vy, vz = v3[0]-v1[0], v3[1]-v1[1], v3[2]-v1[2]
        nx, ny, nz = uy*vz - uz*vy, uz*vx - ux*vz, ux*vy - uy*vx
        length = math.sqrt(nx*nx + ny*ny + nz*nz)
        if length == 0: length = 1
        
        lines.append(f"  facet normal {nx/length:.4f} {ny/length:.4f} {nz/length:.4f}")
        lines.append("    outer loop")
        for v in [v1, v2, v3]:
            lines.append(f"      vertex {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}")
        lines.append("    endloop")
        lines.append("  endfacet")

    # -- TOP PYRAMID (4 Faces) --
    # Connect Top to the 4 waist points
    add_facet(t, f_pt, r)
    add_facet(t, r, bk)
    add_facet(t, bk, l)
    add_facet(t, l, f_pt)

    # -- BOTTOM PYRAMID (4 Faces) --
    # Connect Bottom to the 4 waist points (Reverse winding for outward normals)
    add_facet(b, r, f_pt)
    add_facet(b, bk, r)
    add_facet(b, l, bk)
    add_facet(b, f_pt, l)

    lines.append("endsolid")
    return "\n".join(lines)

def write_stl_file(stl_content):
    with open("model.stl", "w") as f:
        f.write(stl_content)

def write_readme(stl_content):
    readme_text = f"""# 🗿 Collaborative Sculpture

The community is building this shape together. Every update completely rewrites this file!

## Current Shape
Below is the live STL data. GitHub renders this automatically.

[**🌐 View Full Screen 3D Model**]({SITE_URL})

~~~stl
{stl_content}
~~~

## How to Contribute
1. Click the button below.
2. Choose a point and move it!

[ 🛠️ Modify the Mesh ](https://github.com/MatissesProjects/STL-Generator/issues/new?template=modify_mesh.yml)

---
*Last updated by the ShapeBot*
"""
    
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(readme_text)

if __name__ == "__main__":
    state = load_state()
    
    if "ISSUE_BODY" in os.environ:
        v_name, axis_str, amount = parse_issue_body()
        axis_idx = 0
        if "Y" in axis_str: axis_idx = 1
        if "Z" in axis_str: axis_idx = 2
        
        if v_name in state:
            state[v_name][axis_idx] += amount
            with open(STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)

    stl_string = generate_stl_content(state)
    write_stl_file(stl_string)
    write_readme(stl_string)
