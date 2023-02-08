# After trying to practice arch-chroot, I was so annoyed by how annoying mounting BTRFS drives are that I created this very basic script

sudo mount -o subvol=@ /dev/sdXn /mnt

sudo mount -o subvol=@log /dev/sdXn /mnt/var/log

sudo mount -o subvol=@cache /dev/sdXn /mnt/var/cache

sudo mount -o subvol=@home /dev/sdXn /mnt/home
