# Architecture

The system is built on top of the Mesa Abm framework, dividing the simulation into logic, environment, and agents.

## Architecture Diagram

Below is a visual representation of how the major components interact with each other.

```mermaid
classDiagram
    class CyberModel {
        +CyberConfig config
        +NetworkEnvironment network
        +BaseOrganization organization
        +DataCollector datacollector
        +step()
        +count_compromised()
    }

    class NetworkEnvironment {
        +Graph graph
        +Dict nodes
        +get_node()
        +get_random_start_node()
    }

    class BaseOrganization {
        <<abstract>>
        +CyberModel model
        +step()
    }

    class CentralizedOrganization {
        +CyberAgent leader
        +step()
    }

    class SwarmOrganization {
        +step()
    }

    class CyberAgent {
        +CyberNode current_node
        +AgentMemory memory
        +BaseCognition cognition
        +step()
        +execute_action()
    }

    class CyberNode {
        +str id
        +float vulnerability_level
        +int privilege_required
        +bool compromised
    }

    class BaseCognition {
        <<abstract>>
        +decide()
    }

    class RuleBasedCognition {
        +decide()
    }

    CyberModel --> NetworkEnvironment : Owns
    CyberModel --> BaseOrganization : Manages
    CyberModel "1" *-- "*" CyberAgent : Contains
    NetworkEnvironment "1" *-- "*" CyberNode : Contains
    BaseOrganization <|-- CentralizedOrganization
    BaseOrganization <|-- SwarmOrganization
    CyberAgent --> BaseCognition : Uses
    BaseCognition <|-- RuleBasedCognition
    CyberAgent --> CyberNode : Resides on
```

### Component Roles
- **CyberModel:** The central coordinator. Connects the environment, agents, and data collection.
- **NetworkEnvironment:** The space where agents operate. It encapsulates the NetworkX graph and `CyberNode` instances.
- **BaseOrganization (Swarm/Centralized):** Determines if the agents act independently (swarm) or report to a centralized leader.
- **CyberAgent:** The actors carrying out the cyber attacks. They have a basic execution loop that delegates decision-making to their `cognition` module.
- **BaseCognition (RuleBased):** Separates the "brain" of the agent from the "body". It looks at the agent's memory and proposes an action.
