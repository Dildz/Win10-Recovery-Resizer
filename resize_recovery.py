import subprocess
import time

def run_command(command):
    """Runs a command and returns the output"""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {result.stderr}")
        raise Exception(f"Command failed: {command}")
    return result.stdout.strip()

def run_diskpart_commands(commands):
    """Runs a series of diskpart commands"""
    process = subprocess.Popen(['diskpart'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, error = process.communicate(input=commands)
    if process.returncode != 0:
        print(f"Error running command: {error}")
        raise Exception(f"Command failed: {commands}")
    return output.strip()

def confirm_action(prompt):
    """Asks the user to confirm an action"""
    while True:
        response = input(f"{prompt} (Y/N): ").strip().lower()
        if response in ['y', 'n']:
            return response == 'y'
        print("Invalid response, please enter 'Y' or 'N'.")

def get_single_integer(prompt):
    """Asks the user for a single integer input"""
    while True:
        try:
            value = int(input(prompt).strip())
            return value
        except ValueError:
            print("Invalid input, please enter a single integer.")

def main():
    try:
        print("Starting diskpart...")

        # Step 1: List disks
        disks = run_diskpart_commands("list disk\n")
        print(disks)
        
        # Step 2: Select disk
        disk_index = get_single_integer("Enter the OS disk index: ")
        if not confirm_action(f"Confirm selection of disk {disk_index}?"):
            return
        
        # Step 3: Select partition
        partitions = run_diskpart_commands(f"select disk {disk_index}\nlist partition\n")
        print(partitions)
        os_partition_index = get_single_integer("Enter the OS partition index (primary): ")
        if not confirm_action(f"Confirm selection of partition {os_partition_index}?"):
            return
        
        # Step 4: Shrink OS partition
        shrink_output = run_diskpart_commands(f"select disk {disk_index}\nselect partition {os_partition_index}\nshrink desired=250 minimum=250\n")
        print(shrink_output)
        
        # Step 5: Select recovery partition
        partitions = run_diskpart_commands(f"select disk {disk_index}\nlist partition\n")
        print(partitions)
        recovery_partition_index = get_single_integer("Enter the recovery partition index: ")
        if not confirm_action(f"Confirm selection of recovery partition {recovery_partition_index}?"):
            return
        
        # Step 6: Delete recovery partition
        delete_output = run_diskpart_commands(f"select disk {disk_index}\nselect partition {recovery_partition_index}\ndelete partition override\n")
        print(delete_output)
        
        # Step 7: Check if disk is GPT
        disks = run_diskpart_commands("list disk\n")
        print(disks)
        is_gpt = confirm_action("Is there an asterisk in the GPT column?")
        
        # Step 8: Create new recovery partition
        if is_gpt:
            create_output = run_diskpart_commands(f"select disk {disk_index}\ncreate partition primary id=de94bba4-06d1-4d40-a16a-bfd50179d6ac\ngpt attributes=0x8000000000000001\n")
        else:
            create_output = run_diskpart_commands(f"select disk {disk_index}\ncreate partition primary id=27\n")
        print(create_output)
        
        # Step 9: Format the partition
        format_output = run_diskpart_commands(f"select disk {disk_index}\nselect partition {recovery_partition_index}\nformat quick fs=ntfs label='Windows RE tools'\n")
        print(format_output)
        
        # Step 10: Set id for MBR
        if not is_gpt:
            set_id_output = run_diskpart_commands(f"select disk {disk_index}\nselect partition {recovery_partition_index}\nset id=27\n")
            print(set_id_output)
        
        # Step 11: List volumes
        volumes = run_diskpart_commands("list volume\n")
        print(volumes)
        
        if not confirm_action("Is the WinRE partition created?"):
            print("For more information, visit: https://support.microsoft.com/en-us/topic/kb5028997-instructions-to-manually-resize-your-partition-to-install-the-winre-update-400faa27-9343-461c-ada9-24c8229763bf")
            time.sleep(10)
            return
        
        # Step 12: Exit diskpart
        run_diskpart_commands("exit\n")
        
        # Step 13: Re-enable WinRE
        run_command("reagentc /enable")
        
        # Step 14: Confirm WinRE status
        winre_info = run_command("reagentc /info")
        print(winre_info)
        
        time.sleep(5)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
