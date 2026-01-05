To download the testing dataset used for evaluation in our experiments, run the following commands:
```
cd big-vul_dataset
gdown https://drive.google.com/uc?id=1h0iFJbc5DGXCXXvvR6dru_Dms_b2zW4V
```

To download the training and evaluation dataset used for evaluation in our experiments, run the following commands:
```
cd big-vul_dataset
gdown https://drive.google.com/uc?id=1ldXyFvHG41VMrm260cK_JEPYqeb6e6Yw
gdown https://drive.google.com/uc?id=1yggncqivMcP0tzbh8-8Eu02Edwcs44WZ
```

To download the whole (i.e., train+val+test) unsplit dataset dataset, run the following commands:
```
cd big-vul_dataset
gdown https://drive.google.com/uc?id=10-kjbsA806Zdk54Ax8J3WvLKGTzN8CMX
```  

# New Implementation for project thesis

## Transform ReposVul to a LineVul friendly dataset

``cd reposvul_dataset``  
It is expected to download the ReposVul_c dataset of C language and name it : `ReposVul_c.jsonl`.  

``python 01_transform_dataset.py --all_jsonl ReposVul_c.jsonl --out_dir . ``

## Running 03_augment to merge ReposVul with codellama non-vul + vul 

``cd ../llm_datasets``  
``python 03_augment_with_llm.py --raw_train ../reposvul_dataset/train.csv --csv_vuln codellama-34b_vuln.csv --csv_nonvuln codellama-34b_non-vuln.csv --out_dir ../reposvul_with_codellama``  

To augment the raw dataset with only vulnerable samples from llm dataset simply remove the argument ``--csv_nonvuln gpt-4o_non-vuln.csv``    

### Running 03_augment to merge ReposVul with gpt-4o non-vul + vul 

``python 03_augment_with_llm.py --raw_train ../reposvul_dataset/train.csv --csv_vuln gpt-4o_vuln.csv --csv_nonvuln gpt-4o_non-vuln.csv --out_dir ../reposvul_with_gpt-4o``   

To augment the raw dataset with only vulnerable samples from llm dataset simply remove the argument ``--csv_nonvuln gpt-4o_non-vuln.csv``   

## Running 02_transform_dataset to transform PrimeVul Dataset

``cd ../primevul_dataset``  

After Downloading primevul_{train,test,valid}.jsonl in this folder run:  
``python 02_transform_dataset.py --input primevul_train.jsonl --output train.csv``  
``python 02_transform_dataset.py --input primevul_valid.jsonl --output val.csv``  
``python 02_transform_dataset.py --input primevul_test.jsonl --output test.csv``  


## Running 03_augment to merge PrimeVul with codellama non-vul + vul 
``cd ../llm_datasets``

``python 03_augment_with_llm.py --raw_train ../primevul_dataset/train.csv --csv_vuln codellama-34b_vuln.csv --csv_nonvuln codellama-34b_non-vuln.csv --out_dir ../primevul_with_codellama``  

To augment the raw dataset with only vulnerable samples from llm dataset simply remove the argument ``--csv_nonvuln gpt-4o_non-vuln.csv``  

### Running 03_augment to merge PrimeVul with gpt-4o non-vul + vul 

``python 03_augment_with_llm.py --raw_train ../primevul_dataset/train.csv --csv_vuln gpt-4o_vuln.csv --csv_nonvuln gpt-4o_non-vuln.csv --out_dir ../primevul_with_gpt-4o``  

To augment the raw dataset with only vulnerable samples from llm dataset simply remove the argument ``--csv_nonvuln gpt-4o_non-vuln.csv``  

## Running Training Scripts

If you are still in ``llm_datasets`` folder run:  
``cd ../../ ``

You find now 2 Scripts: primevul_train.sh and reposvul_train.sh which run the whole experiment. 

