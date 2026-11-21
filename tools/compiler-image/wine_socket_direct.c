/* Ubuntu 24.04 i386 glibc routes socket operations through legacy
 * socketcall(2), which seccomp BPF cannot inspect by address family.
 * Preload direct Linux i386 socket syscalls inside the sealed rootfs so
 * pool_network.py can keep socketcall(102) denied while permitting AF_UNIX
 * for the local wineserver.
 */
#include <asm/unistd_32.h>

extern long syscall(long number, ...);

int socket(int family, int kind, int protocol)
{
    return syscall(__NR_socket, family, kind, protocol);
}

int socketpair(int family, int kind, int protocol, int *pair)
{
    return syscall(__NR_socketpair, family, kind, protocol, pair);
}

int bind(int fd, const void *address, unsigned int length)
{
    return syscall(__NR_bind, fd, address, length);
}

int connect(int fd, const void *address, unsigned int length)
{
    return syscall(__NR_connect, fd, address, length);
}

int listen(int fd, int backlog)
{
    return syscall(__NR_listen, fd, backlog);
}

int accept4(int fd, void *address, unsigned int *length, int flags)
{
    return syscall(__NR_accept4, fd, address, length, flags);
}

int accept(int fd, void *address, unsigned int *length)
{
    return accept4(fd, address, length, 0);
}

int shutdown(int fd, int how)
{
    return syscall(__NR_shutdown, fd, how);
}

int getsockname(int fd, void *address, unsigned int *length)
{
    return syscall(__NR_getsockname, fd, address, length);
}

int getpeername(int fd, void *address, unsigned int *length)
{
    return syscall(__NR_getpeername, fd, address, length);
}

int setsockopt(int fd, int level, int option, const void *value, unsigned int length)
{
    return syscall(__NR_setsockopt, fd, level, option, value, length);
}

int getsockopt(int fd, int level, int option, void *value, unsigned int *length)
{
    return syscall(__NR_getsockopt, fd, level, option, value, length);
}

long sendmsg(int fd, const void *message, int flags)
{
    return syscall(__NR_sendmsg, fd, message, flags);
}

long recvmsg(int fd, void *message, int flags)
{
    return syscall(__NR_recvmsg, fd, message, flags);
}

long sendto(int fd, const void *buffer, unsigned int count, int flags,
            const void *address, unsigned int length)
{
    return syscall(__NR_sendto, fd, buffer, count, flags, address, length);
}

long recvfrom(int fd, void *buffer, unsigned int count, int flags,
              void *address, unsigned int *length)
{
    return syscall(__NR_recvfrom, fd, buffer, count, flags, address, length);
}

long send(int fd, const void *buffer, unsigned int count, int flags)
{
    return sendto(fd, buffer, count, flags, 0, 0);
}

long recv(int fd, void *buffer, unsigned int count, int flags)
{
    return recvfrom(fd, buffer, count, flags, 0, 0);
}

/* Wine's Ubuntu 24.04 i386 build imports these time64 entry points for local
 * wineserver messaging and control options. The Unix socket operations used
 * by Wine carry no timestamp payload.
 */
long __recvmsg64(int fd, void *message, int flags)
{
    return syscall(__NR_recvmsg, fd, message, flags);
}

long __sendmsg64(int fd, const void *message, int flags)
{
    return syscall(__NR_sendmsg, fd, message, flags);
}

int __getsockopt64(int fd, int level, int option, void *value, unsigned int *length)
{
    return syscall(__NR_getsockopt, fd, level, option, value, length);
}
