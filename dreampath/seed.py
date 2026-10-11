"""Starter content: five streams and a curated, weighted roadmap for each.

Each step is (phase, title, duration_min, weight, min_tier). The video link is
a YouTube search for the topic so it never goes stale; faculty can replace any
of them with a specific, verified video from the Faculty page.
"""
from urllib.parse import quote_plus

STREAMS = [
    ("cse", "Computer Science & Engineering",
     "Software, systems and data.",
     "Programming, data structures, databases and system design for software and product roles."),
    ("ece", "Electronics & Communication",
     "Circuits, embedded and communication.",
     "Analog and digital electronics, embedded systems, VLSI and communication systems."),
    ("eee", "Electrical & Electronics",
     "Machines, power and control.",
     "Electrical machines, power systems, control and the fast-growing EV and renewables space."),
    ("mech", "Mechanical Engineering",
     "Design, thermal and manufacturing.",
     "Mechanics, thermodynamics, CAD/CAE and manufacturing for core and automation roles."),
    ("civil", "Civil Engineering",
     "Structures, geotech and construction.",
     "Structural analysis, design, surveying, estimation and modern BIM tooling."),
]

ROADMAPS = {
    "cse": [
        (1, "C programming for beginners", 480, 6, 0),
        (1, "Git and GitHub crash course", 70, 3, 0),
        (1, "HTML, CSS and JavaScript basics", 300, 4, 0),
        (2, "Data structures and algorithms", 900, 10, 0),
        (2, "Object oriented programming concepts", 240, 6, 0),
        (2, "DBMS and SQL", 300, 7, 0),
        (2, "Operating systems fundamentals", 360, 6, 1),
        (2, "Computer networks essentials", 300, 5, 1),
        (3, "Build a full stack web project", 420, 8, 0),
        (3, "Competitive programming patterns", 360, 6, 1),
        (3, "System design basics", 300, 7, 2),
        (4, "Aptitude and logical reasoning", 240, 4, 0),
        (4, "Mock interviews and HR questions", 120, 5, 0),
        (4, "Resume building for software roles", 60, 4, 0),
        (5, "High level and low level system design", 480, 8, 2),
        (5, "Docker and cloud fundamentals", 300, 6, 2),
        (5, "Machine learning foundations", 600, 6, 3),
        (5, "Contributing to open source", 120, 5, 3),
    ],
    "ece": [
        (1, "Basic electronics and circuit analysis", 360, 7, 0),
        (1, "Digital electronics fundamentals", 300, 7, 0),
        (1, "C programming basics", 240, 4, 0),
        (2, "Analog electronics and op-amps", 300, 6, 0),
        (2, "Signals and systems", 420, 7, 0),
        (2, "Microprocessors 8085 and 8086", 240, 5, 1),
        (2, "Communication systems", 360, 6, 1),
        (3, "Arduino and sensor projects", 180, 7, 0),
        (3, "Embedded C with ARM Cortex", 480, 8, 1),
        (3, "Verilog and FPGA basics", 360, 7, 2),
        (4, "Core electronics interview questions", 150, 6, 0),
        (4, "Aptitude preparation", 240, 4, 0),
        (4, "Resume building for core roles", 60, 3, 0),
        (5, "VLSI design flow", 480, 8, 2),
        (5, "RTOS and embedded Linux", 360, 7, 2),
        (5, "5G and wireless fundamentals", 300, 5, 3),
        (5, "Python for signal processing", 240, 5, 3),
    ],
    "eee": [
        (1, "Basic electrical engineering", 360, 7, 0),
        (1, "Network theory and circuit analysis", 300, 6, 0),
        (1, "Engineering mathematics for EEE", 300, 4, 0),
        (2, "Electrical machines", 480, 8, 0),
        (2, "Power systems", 480, 8, 0),
        (2, "Control systems", 360, 7, 1),
        (2, "Power electronics", 360, 7, 1),
        (3, "MATLAB and Simulink basics", 240, 6, 0),
        (3, "PLC and SCADA programming", 300, 7, 1),
        (3, "Solar PV system design project", 240, 6, 2),
        (4, "Core electrical interview questions", 150, 6, 0),
        (4, "Aptitude preparation", 240, 4, 0),
        (4, "GATE and PSU exam strategy", 90, 4, 1),
        (5, "Electric vehicles and battery systems", 300, 7, 2),
        (5, "Smart grid and renewable integration", 300, 6, 3),
        (5, "Python for energy data analysis", 240, 5, 3),
    ],
    "mech": [
        (1, "Engineering mechanics", 420, 7, 0),
        (1, "Engineering drawing and AutoCAD basics", 300, 5, 0),
        (1, "Thermodynamics fundamentals", 360, 6, 0),
        (2, "Strength of materials", 420, 7, 0),
        (2, "Fluid mechanics", 360, 6, 0),
        (2, "Theory of machines", 360, 6, 1),
        (2, "Manufacturing processes", 300, 6, 1),
        (3, "SolidWorks CAD modelling project", 360, 8, 0),
        (3, "ANSYS finite element analysis basics", 300, 7, 2),
        (3, "3D printing and rapid prototyping", 180, 5, 1),
        (4, "Mechanical interview questions", 150, 6, 0),
        (4, "Aptitude preparation", 240, 4, 0),
        (4, "GATE mechanical strategy", 90, 4, 1),
        (5, "Robotics and automation basics", 360, 6, 2),
        (5, "Computational fluid dynamics fundamentals", 300, 6, 3),
        (5, "Industry 4.0 and IoT in manufacturing", 180, 5, 3),
    ],
    "civil": [
        (1, "Surveying basics", 300, 6, 0),
        (1, "Engineering mechanics for civil", 360, 6, 0),
        (1, "Building materials and construction", 240, 5, 0),
        (2, "Structural analysis", 480, 8, 0),
        (2, "RCC design", 480, 8, 0),
        (2, "Geotechnical engineering", 360, 6, 1),
        (2, "Hydraulics and fluid mechanics", 360, 6, 1),
        (3, "AutoCAD for civil drawings", 240, 6, 0),
        (3, "STAAD Pro structural modelling", 300, 8, 1),
        (3, "Revit and BIM project", 300, 7, 2),
        (4, "Civil interview questions", 150, 6, 0),
        (4, "Aptitude preparation", 240, 4, 0),
        (4, "Estimation and costing", 240, 6, 1),
        (5, "Project management with Primavera", 300, 6, 2),
        (5, "Transportation and highway engineering", 360, 5, 2),
        (5, "Sustainable and green building design", 240, 5, 3),
    ],
}


def video_url(title: str) -> str:
    return "https://www.youtube.com/results?search_query=" + quote_plus(title + " tutorial")


def seed_streams_and_steps(conn) -> None:
    """Insert streams and steps once. Safe to call on every start."""
    if conn.execute("SELECT 1 FROM streams LIMIT 1").fetchone():
        return
    for slug, name, tagline, description in STREAMS:
        conn.execute(
            "INSERT INTO streams (slug, name, tagline, description) VALUES (?, ?, ?, ?)",
            (slug, name, tagline, description),
        )
    for slug, steps in ROADMAPS.items():
        stream_id = conn.execute("SELECT id FROM streams WHERE slug = ?", (slug,)).fetchone()[0]
        for position, (phase, title, minutes, weight, tier) in enumerate(steps):
            conn.execute(
                "INSERT INTO steps (stream_id, phase, position, title, url, duration_min, weight, min_tier) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (stream_id, phase, position, title, video_url(title), minutes, weight, tier),
            )
