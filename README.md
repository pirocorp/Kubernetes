# Kubernetes

## Containerization

**OS-level virtualization** refers to an operating system paradigm in which the kernel allows the existence of multiple isolated user space instances known as containers, zones, jails, ...

On Unix-like operating systems, this feature can be seen as an advanced implementation of the standard chroot mechanism, which changes the apparent root folder for the current running process and its children. In addition to **isolation** mechanisms, the kernel often provides **resource-management features** to limit the impact of one container's activities on other containers.

With **operating-system-virtualization**, or **containerization**, it is possible to run programs within containers, to which only **parts of these resources are allocated**. A program expecting to see the whole computer, once run inside a container, can only see the allocated resources and believes them to be all that is available. Several containers can be created on each operating system, to each of which a subset of the computer's resources is allocated. Each **container may contain any number of computer programs**. These programs may run concurrently or separately, and may even interact with one another.

**Operating-system-level virtualization** is commonly used in virtual **hosting environments**, where it is useful for **securely allocating** finite **hardware** resources among a large number of mutually-distrusting users. System administrators may also use it for consolidating server hardware by moving services on separate hosts into containers on the one server.

Other typical scenarios include separating several programs to separate containers for **improved security**, **hardware independence**, and added **resource management features**. The improved security provided by the use of a chroot mechanism, however, is nowhere near ironclad. Operating-system-level virtualization implementations capable of live migration can also be used for **dynamic load balancing** of **containers between nodes in a cluster**.

**Operating-system-level virtualization** usually imposes **less overhead than full virtualization** because programs in OS-level virtual partitions use the operating system's normal system call interface and do not need to be subjected to emulation or be run in an intermediate virtual machine, as is the case with full virtualization (such as VMware ESXi, QEMU, or Hyper-V) 
