
with open("sample_convo_2.txt", 'r') as f:
    for line in f:
        # if 'User: ' in line:
        #     print(line[6:].strip())
        if 's]' in line:
            print(line.strip())