package agent_policy

default AddARPNeighborsRequest := true
default AddSwapRequest := false
default CloseStdinRequest := false
default CopyFileRequest := false
default CreateContainerRequest := true
default CreateSandboxRequest := true
default DestroySandboxRequest := true
default ExecProcessRequest := false
default GetDiagnosticDataRequest := false
default GetMetricsRequest := true
default GetOOMEventRequest := true
default GuestDetailsRequest := true
default ListInterfacesRequest := true
default ListRoutesRequest := true
default MemHotplugByProbeRequest := true
default OnlineCPUMemRequest := true
default PauseContainerRequest := false
default PullImageRequest := true
default ReadStreamRequest := false
default RemoveContainerRequest := true
default RemoveStaleVirtiofsShareMountsRequest := true
default ReseedRandomDevRequest := false
default ResumeContainerRequest := false
default SetGuestDateTimeRequest := false
default SetPolicyRequest := false
default SignalProcessRequest := true
default StartContainerRequest := true
default StartTracingRequest := false
default StatsContainerRequest := true
default StopTracingRequest := false
default TtyWinResizeRequest := false
default UpdateContainerRequest := true
default UpdateEphemeralMountsRequest := false
default UpdateInterfaceRequest := true
default UpdateRoutesRequest := true
default WaitProcessRequest := true
default WriteStreamRequest := false

copy_file_leaf := ["resolv.conf", "hostname", "hosts", "termination-log"]

CopyFileRequest if {
	startswith(input.path, "/run/kata-containers/shared/containers/")
	some i
	endswith(input.path, copy_file_leaf[i])
	not contains(input.path, "..")
}
