"""The agent's side of the privileged network helper: the wire protocol, the client that speaks
it, and the per-session cluster resolver the agent itself runs.

Separate from the daemon (``ai.backend.agent.network.privnet``) on purpose. This half is the
contract -- what an agent needs in order to ask a helper for privileged work -- and it stays with
the agent whether or not any helper is installed on the node. The daemon that answers is a
deployment's choice, and ships with the data-plane backends it serves.
"""
