from core.templates import ServiceTemplate
from config.hierarchy import SYSTEM_HIERARCHY

# Create service templates based on hierarchy
def create_service_templates():
    templates = {}
    
    # Create coordinator (Atlas)
    templates["atlas"] = ServiceTemplate.create_coordinator(
        name="atlas",
        port=8000
    )

    # Create branch coordinators and their services
    for branch_name, branch in SYSTEM_HIERARCHY.branches.items():
        # Create branch coordinator
        templates[branch.coordinator] = ServiceTemplate.create_branch(
            name=branch.coordinator,
            port=8001 if branch.coordinator == "nova" else 8004,  # Example port assignment
            parent="atlas"
        )
        
        # Create leaf services for each level
        for level in branch.levels:
            for service in level.services:
                templates[service] = ServiceTemplate.create_leaf(
                    name=service,
                    port=get_port_for_service(service),  # Helper function needed
                    parent=branch.coordinator
                )
                
                # Update parent's child queues
                templates[branch.coordinator].messaging_config.child_queues.append(
                    f"{service}_queue"
                )

    return templates

def get_port_for_service(service: str) -> int:
    """Helper function to assign ports to services"""
    port_map = {
        "echo": 8002,
        "pixel": 8003,
        "quantum": 8005
    }
    return port_map.get(service, 8010)  # Default port if not found

# Create all service templates
SERVICE_TEMPLATES = create_service_templates()