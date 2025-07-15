# Kernel Lifecycle Refactoring Sprint Plan

## Overview
This document outlines the remaining work for refactoring the Agent's kernel creation process according to the BEP (Backend Enhancement Proposal) using the new Stage and Provisioner architecture.

## Current State
The kernel creation process in `src/ai/backend/agent/agent.py::create_kernel()` has been partially refactored to use the Stage/Provisioner pattern. Several stages have been implemented, but key stages are still missing.

## Sprint Goals
Complete the kernel lifecycle refactoring by implementing all missing stages and integrating them into the kernel creation flow.

## Sprint Backlog

### Sprint 1: Core Stage Implementation
**Duration**: 1 week

#### Task 1.1: Accelerator Mount Stage
- **File**: `src/ai/backend/agent/stage/kernel_lifecycle/docker/mount/accelerator.py`
- **Status**: ✅ Completed - Separated accelerator mounting into its own stage
- **Classes implemented**:
  - `AcceleratorMountSpec`: Contains config_dir, computers, and resource_spec
  - `AcceleratorMountProvisioner`: Generates accelerator mounts from allocated resources
  - `AcceleratorMountStage`: Stage wrapper for accelerator mount provisioning
- **Key responsibilities**:
  - Generate mounts for all allocated accelerator devices
  - Convert MountInfo to Mount objects with appropriate permissions
  - Work with resource allocations from ResourceStage

#### Task 1.2: Command Arguments Stage
- **File**: Update existing `src/ai/backend/agent/stage/kernel_lifecycle/docker/cmdarg.py`
- **Classes to implement**:
  - `CmdArgStage`: Create stage wrapper for existing `CmdArgProvisioner`
- **Key responsibilities**:
  - Manage command argument provisioning lifecycle
  - Integrate with the stage pipeline

### Sprint 2: Container Preparation and Lifecycle Stages
**Duration**: 2 weeks

#### Task 2.1: Refactor prepare_container() into Stages
The current `prepare_container()` function in `src/ai/backend/agent/docker/agent.py` performs multiple responsibilities that should be broken down into separate stages:

##### Task 2.1.1: Bootstrap Stage
- **File**: `src/ai/backend/agent/stage/kernel_lifecycle/docker/bootstrap.py`
- **Classes to implement**:
  - `BootstrapProvisioner`: Handle bootstrap script creation
  - `BootstrapStage`: Manage bootstrap provisioner
- **Key responsibilities**:
  - Create bootstrap.sh file if provided in kernel config
  - Set appropriate ownership and permissions

##### Task 2.1.2: Config Files Stage
- **File**: `src/ai/backend/agent/stage/kernel_lifecycle/docker/config_files.py`
- **Classes to implement**:
  - `ConfigFileProvisioner`: Create environment and resource configuration files
  - `ConfigFileStage`: Manage config file provisioner
- **Key responsibilities**:
  - Write environment variables to environ.txt
  - Write resource specifications to resource.txt
  - Create backup files (environ_base.txt, resource_base.txt)

##### Task 2.1.3: Credentials Stage
- **File**: `src/ai/backend/agent/stage/kernel_lifecycle/docker/credentials.py`
- **Classes to implement**:
  - `CredentialsProvisioner`: Handle Docker credentials and authentication
  - `CredentialsStage`: Manage credentials provisioner
- **Key responsibilities**:
  - Write Docker credentials to docker-creds.json if provided

##### Task 2.1.4: Container SSH Stage
- **File**: `src/ai/backend/agent/stage/kernel_lifecycle/docker/container_ssh.py`
- **Classes to implement**:
  - `ContainerSSHProvisioner`: Set up SSH keys inside container work directory
  - `ContainerSSHStage`: Manage container SSH provisioner
- **Key responsibilities**:
  - Create SSH keypair files in container work directory
  - Set up .ssh directory structure
  - Configure authorized_keys, id_rsa, and id_container files
  - Note: This is different from existing SSHStage which handles cluster SSH

##### Task 2.1.5: Dotfiles Stage
- **File**: `src/ai/backend/agent/stage/kernel_lifecycle/docker/dotfiles.py`
- **Classes to implement**:
  - `DotfilesProvisioner`: Process and install dotfiles
  - `DotfilesStage`: Manage dotfiles provisioner
- **Key responsibilities**:
  - Process all dotfiles from internal_data
  - Create directory structures as needed
  - Set appropriate permissions and ownership

##### Task 2.1.6: Kernel Object Creation Stage
- **File**: `src/ai/backend/agent/stage/kernel_lifecycle/docker/kernel_object.py`
- **Classes to implement**:
  - `KernelObjectProvisioner`: Create final DockerKernel object
  - `KernelObjectStage`: Manage kernel object provisioner
- **Key responsibilities**:
  - Create DockerKernel instance with all prepared configurations
  - Initialize kernel with proper metadata

#### Task 2.2: Container Creation Stage
- **File**: `src/ai/backend/agent/stage/kernel_lifecycle/docker/container.py`
- **Classes to implement**:
  - `ContainerCreationProvisioner`: Handle actual container creation
  - `ContainerCreationStage`: Manage container creation provisioner
- **Key responsibilities**:
  - Create the Docker container with all configurations
  - Apply all collected settings from previous stages
  - Handle container creation errors gracefully

#### Task 2.3: Container Verification Stage
- **File**: `src/ai/backend/agent/stage/kernel_lifecycle/docker/verify.py`
- **Classes to implement**:
  - `ContainerVerificationProvisioner`: Verify container health
  - `ContainerVerificationStage`: Manage verification provisioner
- **Key responsibilities**:
  - Check container is running properly
  - Verify kernel process is healthy
  - Validate all expected services are available
  - Report any initialization failures

### Sprint 3: Integration and Testing
**Duration**: 1 week

#### Task 3.1: Stage Pipeline Integration
- **File**: Update `src/ai/backend/agent/agent.py`
- **Actions**:
  - Create complete stage pipeline for kernel creation
  - Replace existing create_kernel() logic with stage-based approach
  - Ensure backward compatibility

#### Task 3.2: Unit Tests
- **Files**: Create test files in appropriate test directories
- **Tests to implement**:
  - Test each new stage individually
  - Test stage pipeline integration
  - Test error handling and rollback scenarios

#### Task 3.3: Integration Tests
- **Actions**:
  - Test complete kernel creation flow
  - Verify all stages work together correctly
  - Test various kernel configurations (GPU, CPU-only, different images)

## Technical Considerations

### Stage Order
The recommended stage execution order for kernel creation:
1. ImagePullStage
2. ResourceStage
3. EnvironStage
4. IntrinsicMountStage
5. ScratchStage
6. NetworkStage
7. SSHStage (if enabled)
8. VFolderMountStage
9. AcceleratorMountStage
10. KernelRunnerMountStage
11. ServiceProvisioner/ModelServiceProvisioner
12. BootstrapStage
13. ConfigFileStage
14. CredentialsStage
15. ContainerSSHStage (if ssh_keypair in internal_data)
16. DotfilesStage
17. CmdArgStage
18. KernelObjectStage
19. ContainerCreationStage
20. ContainerVerificationStage

### Error Handling
- Each stage must implement proper rollback in case of failure
- The pipeline should gracefully handle stage failures
- Resource cleanup must be guaranteed even on failure

### Performance Considerations
- Stages that can run in parallel should be identified
- Consider implementing parallel stage execution where possible
- Monitor and optimize stage execution times

### Refactoring prepare_container() - Additional Considerations

#### Shared Utilities
- **File**: `src/ai/backend/agent/stage/kernel_lifecycle/docker/utils.py`
- **Functions to implement**:
  - `chown_paths_if_root()`: Extract the ownership management logic
  - `ensure_directory_exists()`: Common directory creation logic
  - `write_file_with_permissions()`: Common file writing with permission handling

#### State Management Between Stages
- Use a shared context object to pass data between stages
- Context should include:
  - `work_dir`: Container work directory path
  - `config_dir`: Container config directory path
  - `kernel_config`: Complete kernel configuration
  - `internal_data`: Internal configuration data
  - `uid_override`/`gid_override`: Ownership overrides
  - `container_info`: Information gathered during container preparation
  - `resource_spec`: KernelResourceSpec with allocations

#### Migration Strategy
1. Implement all new stages in parallel with existing `prepare_container()`
2. Create comprehensive tests comparing outputs of both approaches
3. Gradually migrate to stage-based approach with feature flags
4. Remove `prepare_container()` once all stages are proven stable

## Definition of Done
- [x] AcceleratorMountStage created to handle accelerator mount generation
- [x] Resource allocation and accelerator mounting properly separated
- [ ] All missing stages implemented with both Provisioner and Stage classes
- [ ] prepare_container() function refactored into separate stages
- [ ] create_kernel() function refactored to use stage pipeline
- [ ] All unit tests passing
- [ ] Integration tests covering major scenarios
- [ ] Documentation updated to reflect new architecture
- [ ] Code review completed and feedback addressed
- [ ] Performance benchmarks show no regression

## Future Enhancements
- Implement parallel stage execution framework
- Add stage metrics and monitoring
- Create stage dependency graph visualization
- Implement stage plugin system for custom stages

## Directions
- DO NOT use `ai.backend.agent.AbstractAgent` or its subclass in stage refactored codes
- No need to add example codes
- No need to write test codes
