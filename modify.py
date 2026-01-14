import json
import os
import math

STATE_FILE = "state.json"
STL_FILE = "model.stl"

def load_state():
    # Default 'clean' crystal if state is missing
    if not os.path.exists(STATE_FILE):
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
    
    # Parse the form data
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

def generate_stl(state):
    # Unpack vertices for easy access
    t = state["top"]
    b = state["bottom"]
    w1 = state["waist_1"]
    w2 = state["waist_2"]
    w3 = state["waist_3"]
    w4 = state["waist_4"]

    with open(STL_FILE, "w") as f:
        f.write("solid sculpted_mesh\n")

        # Helper to write a triangle
        def write_facet(v1, v2, v3):
            # Calculate normal
            ux, uy, uz = v2[0]-v1[0], v2[1]-v1[1], v2[2]-v1[2]
            vx, vy, vz = v3[0]-v1[0], v3[1]-v1[1], v3[2]-v1[2]
            nx, ny, nz = uy*vz - uz*vy, uz*vx - ux*vz, ux*vy - uy*vx
            l = math.sqrt(nx*nx + ny*ny + nz*nz)
            if l == 0: l = 1 # Avoid div by zero
            
            f.write(f"  facet normal {nx/l:.4f} {ny/l:.4f} {nz/l:.4f}\n")
            f.write("    outer loop\n")
            for v in [v1, v2, v3]:
                f.write(f"      vertex {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
            f.write("    endloop\n  endfacet\n")

        # Top Pyramid Faces
        write_facet(t, w1, w2)
        write_facet(t, w2, w3)
        write_facet(t, w3, w4)
        write_facet(t, w4, w1)

        # Bottom Pyramid Faces (winding order reversed)
        write_facet(b, w2, w1)
        write_facet(b, w3, w2)
        write_facet(b, w4, w3)
        write_facet(b, w1, w4)

        f.write("endsolid")

if __name__ == "__main__":
    state = load_state()
    
    if "ISSUE_BODY" in os.environ:
        v_name, axis_str, amount = parse_issue_body()
        
        # Map axis name to index (0=x, 1=y, 2=z)
        axis_idx = 0
        if "Y" in axis_str: axis_idx = 1
        if "Z" in axis_str: axis_idx = 2
        
        if v_name in state:
            state[v_name][axis_idx] += amount
            print(f"Moved {v_name} by {amount} on axis {axis_idx}")
            
            # Save updated state
            with open(STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)

    generate_stl(state)
