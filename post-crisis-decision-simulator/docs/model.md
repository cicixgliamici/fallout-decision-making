# Model

A community consists of agents, scarce resources, a trust graph, and repeated policy decisions.

## Agents

Each agent has:

- name
- role
- health
- risk aversion
- cooperation level
- preference ranking over policies
- survival status
- sanction status

## Policies

The available policies are:

- farming
- medicine
- defense
- exploration

Each policy changes the community state differently. Farming improves food supply; medicine improves health; defense improves security; exploration can discover resources but introduces risk.

## Metrics

The simulator measures:

- survival rate
- social welfare
- health inequality
- final resource levels
