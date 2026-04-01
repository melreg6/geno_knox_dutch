# GenoCAD → Knox Grammar Rule Engine
### EC552 Project — geno_knox_dutch (Ongoing Project) 

This project extracts construct grammar from GenoCAD, translates it into Goldbar rules, and submits those rules to Knox for valid design enumeration.

---

## What It Does

1. **Extracts** grammar rules from a GenoCAD SQL database
2. **Translates** those rules into Goldbar expressions
3. **Submits** the Goldbar rules to the Knox API
4. **Enumerates** all valid part combinations Knox returns

---

## File Structure

```
EC552_Project/
│
├── grammar_rule_engine/
│   ├── __init__.py
│   ├── genocad_grammar_extractor.py   
│   ├── goldbar_translator.py          
│   └── knox_interface.py              
│
├── tests/
│   ├── test_extractor.py              
│   ├── test_translator.py            
│   └── test_knox.py                 
│
├── data/
│   └── genocad.db                     
│
├── docs/
│   └── genocad_goldbar_pipeline.svg   
│
├── other files (TBD)
└── README.md                          ← this file
```

---

## Pipeline Flow

```
GenoCAD SQL DB
      ↓  extract()
 GrammarRule objects
      ↓  translate_all()
 Goldbar strings
      ↓  submit_rules()
 Knox API  →  POST /rules
      ↓  enumerate_designs()
 Valid designs  →  GET /enumerate
```



## Team Members
 
Varsha Athreya, 
Melissa Regalado, 
Paulina Garcia, 
Denalda Gashi
