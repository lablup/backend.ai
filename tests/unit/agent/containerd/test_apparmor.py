"""The AppArmor profile the containerd backend loads to match dockerd's docker-default."""

from ai.backend.agent.containerd.apparmor import PROFILE_NAME, render_profile


class TestProfile:
    def test_the_peer_rules_name_the_profile(self) -> None:
        # The signal/ptrace peer names must be the profile's own name, or a container's processes
        # cannot signal or `ps` each other.
        profile = render_profile("some-name")
        assert "profile some-name flags=" in profile
        assert "signal (send,receive) peer=some-name," in profile
        assert "ptrace (trace,read,tracedby,readby) peer=some-name," in profile

    def test_it_denies_the_ways_out_of_the_container(self) -> None:
        profile = render_profile(PROFILE_NAME)
        for rule in (
            "deny @{PROC}/sysrq-trigger rwklx,",  # reboot the host
            "deny @{PROC}/kcore rwklx,",  # read host memory
            "deny /sys/firmware/** rwklx,",
            "deny /sys/kernel/security/** rwklx,",  # unload the profile itself
            "deny mount,",
        ):
            assert rule in profile, rule

    def test_a_host_process_may_still_signal_into_the_container(self) -> None:
        # The agent stops kernels by signalling them; a profile that blocked that would leave every
        # kernel to be SIGKILLed after its grace period.
        assert "signal (receive) peer=unconfined," in render_profile(PROFILE_NAME)
