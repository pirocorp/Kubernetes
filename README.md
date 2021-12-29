# Kubernetes

## Containerization

**OS-level virtualization** refers to an operating system paradigm in which the kernel allows the existence of multiple isolated user space instances known as containers, zones, jails, ...

On Unix-like operating systems, this feature can be seen as an advanced implementation of the standard chroot mechanism, which changes the apparent root folder for the current running process and its children. In addition to **isolation** mechanisms, the kernel often provides **resource-management features** to limit the impact of one container's activities on other containers.

With **operating-system-virtualization**, or **containerization**, it is possible to run programs within containers, to which only **parts of these resources are allocated**. A program expecting to see the whole computer, once run inside a container, can only see the allocated resources and believes them to be all that is available. Several containers can be created on each operating system, to each of which a subset of the computer's resources is allocated. Each **container may contain any number of computer programs**. These programs may run concurrently or separately, and may even interact with one another.

**Operating-system-level virtualization** is commonly used in virtual **hosting environments**, where it is useful for **securely allocating** finite **hardware** resources among a large number of mutually-distrusting users. System administrators may also use it for consolidating server hardware by moving services on separate hosts into containers on the one server.

Other typical scenarios include separating several programs to separate containers for **improved security**, **hardware independence**, and added **resource management features**. The improved security provided by the use of a chroot mechanism, however, is nowhere near ironclad. Operating-system-level virtualization implementations capable of live migration can also be used for **dynamic load balancing** of **containers between nodes in a cluster**.

**Operating-system-level virtualization** usually imposes **less overhead than full virtualization** because programs in OS-level virtual partitions use the operating system's normal system call interface and do not need to be subjected to emulation or be run in an intermediate virtual machine, as is the case with full virtualization (such as VMware ESXi, QEMU, or Hyper-V) 

![image](https://user-images.githubusercontent.com/34960418/147653601-f596fcdf-78ed-4b31-8e79-bb6c5b674a25.png)

## Docker Container

A **container** is a **standard unit of software that packages up code and all its dependencies** so the application runs quickly and reliably from one computing environment to another. A Docker container image is a lightweight, standalone, executable package of software that includes everything needed to run an application: code, runtime, system tools, system libraries and settings.

**Container images become containers at runtime** and in the case of Docker containers - images become containers when they run on Docker Engine. Available for both Linux and Windows-based applications, containerized software will always run the same, regardless of the infrastructure. Containers isolate software from its environment and ensure that it works uniformly despite differences for instance between development and staging.

![image](https://user-images.githubusercontent.com/34960418/147654316-422a936c-9489-4eb0-90fd-d89153f2f7b4.png)

- **Container** - A runnable instance of an image. Containers are processes with much more isolation.
- **Image** - A read-only template of a container built from layers. Images provide a way for simpler software distribution
- **Repository** - A collection of different versions of an image identified by tags
- **Registry** - A collection of repositories

## Kubernetes

- Runs a cluster of hosts
- Schedules containers to run on different hosts
- Facilitates the communication between the containers
- Provides and controls access to/from outside world
- Tracks and optimizes the resource usage

