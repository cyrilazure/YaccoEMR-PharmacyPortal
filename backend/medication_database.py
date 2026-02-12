"""
Global Medication Database
==========================
Comprehensive database of medications available in Ghana and worldwide.
Includes generic names, brand names, manufacturers, dosage forms, and classifications.
"""

# Common medications available in Ghana and globally
GLOBAL_MEDICATIONS = [
    # ==========================================
    # ANALGESICS & ANTIPYRETICS
    # ==========================================
    {"generic_name": "Paracetamol", "brand_names": ["Tylenol", "Panadol", "Efpac", "Aeknil"], "category": "analgesic", "dosage_forms": ["tablet", "syrup", "suppository", "injection"], "strengths": ["500mg", "1000mg", "120mg/5ml", "250mg/5ml"]},
    {"generic_name": "Ibuprofen", "brand_names": ["Advil", "Brufen", "Nurofen", "Ibupain"], "category": "nsaid", "dosage_forms": ["tablet", "capsule", "suspension"], "strengths": ["200mg", "400mg", "600mg", "100mg/5ml"]},
    {"generic_name": "Diclofenac", "brand_names": ["Voltaren", "Diclomax", "Rufenal"], "category": "nsaid", "dosage_forms": ["tablet", "injection", "gel", "suppository"], "strengths": ["25mg", "50mg", "75mg", "100mg"]},
    {"generic_name": "Aspirin", "brand_names": ["Bayer", "Disprin", "Ecotrin"], "category": "nsaid", "dosage_forms": ["tablet"], "strengths": ["75mg", "100mg", "300mg", "500mg"]},
    {"generic_name": "Tramadol", "brand_names": ["Ultram", "Tramal", "Contramal"], "category": "opioid_analgesic", "dosage_forms": ["capsule", "injection"], "strengths": ["50mg", "100mg"]},
    {"generic_name": "Morphine", "brand_names": ["MS Contin", "Oramorph"], "category": "opioid_analgesic", "dosage_forms": ["tablet", "injection", "syrup"], "strengths": ["10mg", "15mg", "30mg", "60mg"]},
    {"generic_name": "Codeine", "brand_names": ["Codeine Phosphate"], "category": "opioid_analgesic", "dosage_forms": ["tablet", "syrup"], "strengths": ["15mg", "30mg", "60mg"]},
    {"generic_name": "Naproxen", "brand_names": ["Aleve", "Naprosyn", "Anaprox"], "category": "nsaid", "dosage_forms": ["tablet"], "strengths": ["250mg", "500mg"]},
    {"generic_name": "Celecoxib", "brand_names": ["Celebrex"], "category": "nsaid", "dosage_forms": ["capsule"], "strengths": ["100mg", "200mg"]},
    {"generic_name": "Meloxicam", "brand_names": ["Mobic"], "category": "nsaid", "dosage_forms": ["tablet"], "strengths": ["7.5mg", "15mg"]},
    
    # ==========================================
    # ANTIBIOTICS - PENICILLINS
    # ==========================================
    {"generic_name": "Amoxicillin", "brand_names": ["Amoxil", "Trimox", "Moxatag"], "category": "antibiotic_penicillin", "dosage_forms": ["capsule", "suspension", "tablet"], "strengths": ["250mg", "500mg", "125mg/5ml", "250mg/5ml"]},
    {"generic_name": "Ampicillin", "brand_names": ["Omnipen", "Principen"], "category": "antibiotic_penicillin", "dosage_forms": ["capsule", "injection"], "strengths": ["250mg", "500mg", "1g"]},
    {"generic_name": "Amoxicillin/Clavulanate", "brand_names": ["Augmentin", "Clavamox", "Co-Amoxiclav"], "category": "antibiotic_penicillin", "dosage_forms": ["tablet", "suspension"], "strengths": ["375mg", "625mg", "1g", "228mg/5ml", "457mg/5ml"]},
    {"generic_name": "Flucloxacillin", "brand_names": ["Floxapen", "Fluclox"], "category": "antibiotic_penicillin", "dosage_forms": ["capsule", "injection"], "strengths": ["250mg", "500mg"]},
    {"generic_name": "Penicillin V", "brand_names": ["Pen-Vee K", "Veetids"], "category": "antibiotic_penicillin", "dosage_forms": ["tablet", "suspension"], "strengths": ["250mg", "500mg"]},
    {"generic_name": "Benzylpenicillin", "brand_names": ["Penicillin G"], "category": "antibiotic_penicillin", "dosage_forms": ["injection"], "strengths": ["600mg", "1.2g", "2.4g"]},
    
    # ==========================================
    # ANTIBIOTICS - CEPHALOSPORINS
    # ==========================================
    {"generic_name": "Ceftriaxone", "brand_names": ["Rocephin", "Ceftrex"], "category": "antibiotic_cephalosporin", "dosage_forms": ["injection"], "strengths": ["250mg", "500mg", "1g", "2g"]},
    {"generic_name": "Cefuroxime", "brand_names": ["Zinacef", "Ceftin", "Zinnat"], "category": "antibiotic_cephalosporin", "dosage_forms": ["tablet", "injection", "suspension"], "strengths": ["250mg", "500mg", "750mg", "1.5g"]},
    {"generic_name": "Cefixime", "brand_names": ["Suprax", "Cefix"], "category": "antibiotic_cephalosporin", "dosage_forms": ["capsule", "suspension"], "strengths": ["200mg", "400mg", "100mg/5ml"]},
    {"generic_name": "Cephalexin", "brand_names": ["Keflex", "Cefalex"], "category": "antibiotic_cephalosporin", "dosage_forms": ["capsule", "suspension"], "strengths": ["250mg", "500mg", "125mg/5ml", "250mg/5ml"]},
    {"generic_name": "Cefotaxime", "brand_names": ["Claforan"], "category": "antibiotic_cephalosporin", "dosage_forms": ["injection"], "strengths": ["500mg", "1g", "2g"]},
    {"generic_name": "Ceftazidime", "brand_names": ["Fortaz", "Tazicef"], "category": "antibiotic_cephalosporin", "dosage_forms": ["injection"], "strengths": ["500mg", "1g", "2g"]},
    
    # ==========================================
    # ANTIBIOTICS - MACROLIDES
    # ==========================================
    {"generic_name": "Azithromycin", "brand_names": ["Zithromax", "Azithro", "Z-Pack"], "category": "antibiotic_macrolide", "dosage_forms": ["tablet", "suspension", "injection"], "strengths": ["250mg", "500mg", "200mg/5ml"]},
    {"generic_name": "Erythromycin", "brand_names": ["Erythrocin", "E-Mycin", "Eryc"], "category": "antibiotic_macrolide", "dosage_forms": ["tablet", "suspension", "injection"], "strengths": ["250mg", "500mg", "125mg/5ml", "250mg/5ml"]},
    {"generic_name": "Clarithromycin", "brand_names": ["Biaxin", "Klacid"], "category": "antibiotic_macrolide", "dosage_forms": ["tablet", "suspension"], "strengths": ["250mg", "500mg", "125mg/5ml"]},
    
    # ==========================================
    # ANTIBIOTICS - FLUOROQUINOLONES
    # ==========================================
    {"generic_name": "Ciprofloxacin", "brand_names": ["Cipro", "Ciproxin", "Ciloxan"], "category": "antibiotic_fluoroquinolone", "dosage_forms": ["tablet", "injection", "eye drops"], "strengths": ["250mg", "500mg", "750mg", "200mg/100ml", "0.3%"]},
    {"generic_name": "Levofloxacin", "brand_names": ["Levaquin", "Tavanic"], "category": "antibiotic_fluoroquinolone", "dosage_forms": ["tablet", "injection"], "strengths": ["250mg", "500mg", "750mg"]},
    {"generic_name": "Norfloxacin", "brand_names": ["Noroxin"], "category": "antibiotic_fluoroquinolone", "dosage_forms": ["tablet"], "strengths": ["400mg"]},
    {"generic_name": "Ofloxacin", "brand_names": ["Floxin", "Ocuflox"], "category": "antibiotic_fluoroquinolone", "dosage_forms": ["tablet", "eye drops", "ear drops"], "strengths": ["200mg", "400mg", "0.3%"]},
    {"generic_name": "Moxifloxacin", "brand_names": ["Avelox", "Vigamox"], "category": "antibiotic_fluoroquinolone", "dosage_forms": ["tablet", "eye drops"], "strengths": ["400mg", "0.5%"]},
    
    # ==========================================
    # ANTIBIOTICS - AMINOGLYCOSIDES
    # ==========================================
    {"generic_name": "Gentamicin", "brand_names": ["Garamycin", "Gentak"], "category": "antibiotic_aminoglycoside", "dosage_forms": ["injection", "eye drops", "cream"], "strengths": ["40mg/ml", "80mg/2ml", "0.3%"]},
    {"generic_name": "Amikacin", "brand_names": ["Amikin"], "category": "antibiotic_aminoglycoside", "dosage_forms": ["injection"], "strengths": ["100mg/2ml", "500mg/2ml"]},
    {"generic_name": "Streptomycin", "brand_names": ["Streptomycin Sulfate"], "category": "antibiotic_aminoglycoside", "dosage_forms": ["injection"], "strengths": ["1g"]},
    
    # ==========================================
    # ANTIBIOTICS - OTHERS
    # ==========================================
    {"generic_name": "Metronidazole", "brand_names": ["Flagyl", "Metro", "Metrogyl"], "category": "antibiotic_nitroimidazole", "dosage_forms": ["tablet", "injection", "suppository", "gel"], "strengths": ["200mg", "400mg", "500mg", "500mg/100ml"]},
    {"generic_name": "Clindamycin", "brand_names": ["Cleocin", "Dalacin"], "category": "antibiotic_lincosamide", "dosage_forms": ["capsule", "injection", "gel"], "strengths": ["150mg", "300mg", "600mg"]},
    {"generic_name": "Doxycycline", "brand_names": ["Vibramycin", "Doxycyn"], "category": "antibiotic_tetracycline", "dosage_forms": ["capsule", "tablet"], "strengths": ["50mg", "100mg"]},
    {"generic_name": "Tetracycline", "brand_names": ["Sumycin", "Achromycin"], "category": "antibiotic_tetracycline", "dosage_forms": ["capsule"], "strengths": ["250mg", "500mg"]},
    {"generic_name": "Trimethoprim/Sulfamethoxazole", "brand_names": ["Bactrim", "Septrin", "Co-trimoxazole"], "category": "antibiotic_sulfonamide", "dosage_forms": ["tablet", "suspension", "injection"], "strengths": ["480mg", "960mg", "240mg/5ml"]},
    {"generic_name": "Nitrofurantoin", "brand_names": ["Macrobid", "Macrodantin"], "category": "antibiotic_nitrofuran", "dosage_forms": ["capsule"], "strengths": ["50mg", "100mg"]},
    {"generic_name": "Vancomycin", "brand_names": ["Vancocin"], "category": "antibiotic_glycopeptide", "dosage_forms": ["injection", "capsule"], "strengths": ["500mg", "1g"]},
    
    # ==========================================
    # ANTIMALARIALS
    # ==========================================
    {"generic_name": "Artemether/Lumefantrine", "brand_names": ["Coartem", "Riamet", "Lonart"], "category": "antimalarial", "dosage_forms": ["tablet", "suspension"], "strengths": ["20/120mg", "40/240mg", "80/480mg"]},
    {"generic_name": "Artesunate", "brand_names": ["Artesunat", "Artesun"], "category": "antimalarial", "dosage_forms": ["tablet", "injection", "suppository"], "strengths": ["50mg", "100mg", "200mg", "60mg/ml"]},
    {"generic_name": "Artesunate/Amodiaquine", "brand_names": ["ASAQ", "Coarsucam", "Artesunat-Amodiaquine"], "category": "antimalarial", "dosage_forms": ["tablet"], "strengths": ["25/67.5mg", "50/135mg", "100/270mg"]},
    {"generic_name": "Dihydroartemisinin/Piperaquine", "brand_names": ["Eurartesim", "Duo-Cotecxin", "P-Alaxin"], "category": "antimalarial", "dosage_forms": ["tablet"], "strengths": ["20/160mg", "40/320mg"]},
    {"generic_name": "Quinine", "brand_names": ["Qualaquin", "Quinine Sulfate"], "category": "antimalarial", "dosage_forms": ["tablet", "injection"], "strengths": ["300mg", "600mg", "300mg/ml"]},
    {"generic_name": "Chloroquine", "brand_names": ["Aralen", "Avloclor"], "category": "antimalarial", "dosage_forms": ["tablet", "injection"], "strengths": ["250mg", "500mg"]},
    {"generic_name": "Sulfadoxine/Pyrimethamine", "brand_names": ["Fansidar", "Orodar"], "category": "antimalarial", "dosage_forms": ["tablet"], "strengths": ["500/25mg"]},
    {"generic_name": "Atovaquone/Proguanil", "brand_names": ["Malarone"], "category": "antimalarial", "dosage_forms": ["tablet"], "strengths": ["250/100mg", "62.5/25mg"]},
    {"generic_name": "Mefloquine", "brand_names": ["Lariam"], "category": "antimalarial", "dosage_forms": ["tablet"], "strengths": ["250mg"]},
    {"generic_name": "Primaquine", "brand_names": ["Primaquine Phosphate"], "category": "antimalarial", "dosage_forms": ["tablet"], "strengths": ["7.5mg", "15mg"]},
    
    # ==========================================
    # ANTIHYPERTENSIVES
    # ==========================================
    {"generic_name": "Amlodipine", "brand_names": ["Norvasc", "Amlopin"], "category": "antihypertensive_ccb", "dosage_forms": ["tablet"], "strengths": ["2.5mg", "5mg", "10mg"]},
    {"generic_name": "Lisinopril", "brand_names": ["Zestril", "Prinivil"], "category": "antihypertensive_acei", "dosage_forms": ["tablet"], "strengths": ["2.5mg", "5mg", "10mg", "20mg", "40mg"]},
    {"generic_name": "Enalapril", "brand_names": ["Vasotec", "Renitec"], "category": "antihypertensive_acei", "dosage_forms": ["tablet"], "strengths": ["2.5mg", "5mg", "10mg", "20mg"]},
    {"generic_name": "Losartan", "brand_names": ["Cozaar", "Losartan"], "category": "antihypertensive_arb", "dosage_forms": ["tablet"], "strengths": ["25mg", "50mg", "100mg"]},
    {"generic_name": "Valsartan", "brand_names": ["Diovan"], "category": "antihypertensive_arb", "dosage_forms": ["tablet"], "strengths": ["40mg", "80mg", "160mg", "320mg"]},
    {"generic_name": "Atenolol", "brand_names": ["Tenormin"], "category": "antihypertensive_beta_blocker", "dosage_forms": ["tablet"], "strengths": ["25mg", "50mg", "100mg"]},
    {"generic_name": "Metoprolol", "brand_names": ["Lopressor", "Toprol"], "category": "antihypertensive_beta_blocker", "dosage_forms": ["tablet", "injection"], "strengths": ["25mg", "50mg", "100mg", "200mg"]},
    {"generic_name": "Propranolol", "brand_names": ["Inderal"], "category": "antihypertensive_beta_blocker", "dosage_forms": ["tablet", "injection"], "strengths": ["10mg", "40mg", "80mg"]},
    {"generic_name": "Nifedipine", "brand_names": ["Adalat", "Procardia"], "category": "antihypertensive_ccb", "dosage_forms": ["tablet", "capsule"], "strengths": ["10mg", "20mg", "30mg", "60mg"]},
    {"generic_name": "Hydrochlorothiazide", "brand_names": ["Microzide", "HydroDIURIL"], "category": "antihypertensive_diuretic", "dosage_forms": ["tablet"], "strengths": ["12.5mg", "25mg", "50mg"]},
    {"generic_name": "Furosemide", "brand_names": ["Lasix", "Frusemide"], "category": "diuretic_loop", "dosage_forms": ["tablet", "injection"], "strengths": ["20mg", "40mg", "80mg", "10mg/ml"]},
    {"generic_name": "Spironolactone", "brand_names": ["Aldactone"], "category": "diuretic_potassium_sparing", "dosage_forms": ["tablet"], "strengths": ["25mg", "50mg", "100mg"]},
    {"generic_name": "Bisoprolol", "brand_names": ["Zebeta", "Concor"], "category": "antihypertensive_beta_blocker", "dosage_forms": ["tablet"], "strengths": ["2.5mg", "5mg", "10mg"]},
    {"generic_name": "Carvedilol", "brand_names": ["Coreg"], "category": "antihypertensive_beta_blocker", "dosage_forms": ["tablet"], "strengths": ["3.125mg", "6.25mg", "12.5mg", "25mg"]},
    {"generic_name": "Telmisartan", "brand_names": ["Micardis"], "category": "antihypertensive_arb", "dosage_forms": ["tablet"], "strengths": ["20mg", "40mg", "80mg"]},
    {"generic_name": "Ramipril", "brand_names": ["Altace", "Tritace"], "category": "antihypertensive_acei", "dosage_forms": ["capsule"], "strengths": ["1.25mg", "2.5mg", "5mg", "10mg"]},
    
    # ==========================================
    # ANTIDIABETICS
    # ==========================================
    {"generic_name": "Metformin", "brand_names": ["Glucophage", "Glycomet", "Diaformin"], "category": "antidiabetic_biguanide", "dosage_forms": ["tablet"], "strengths": ["500mg", "850mg", "1000mg"]},
    {"generic_name": "Glibenclamide", "brand_names": ["Daonil", "Glyburide", "Diabeta"], "category": "antidiabetic_sulfonylurea", "dosage_forms": ["tablet"], "strengths": ["2.5mg", "5mg"]},
    {"generic_name": "Gliclazide", "brand_names": ["Diamicron", "Glizid"], "category": "antidiabetic_sulfonylurea", "dosage_forms": ["tablet"], "strengths": ["30mg", "60mg", "80mg"]},
    {"generic_name": "Glimepiride", "brand_names": ["Amaryl"], "category": "antidiabetic_sulfonylurea", "dosage_forms": ["tablet"], "strengths": ["1mg", "2mg", "4mg"]},
    {"generic_name": "Insulin Regular", "brand_names": ["Humulin R", "Novolin R", "Actrapid"], "category": "antidiabetic_insulin", "dosage_forms": ["injection"], "strengths": ["100 IU/ml"]},
    {"generic_name": "Insulin NPH", "brand_names": ["Humulin N", "Novolin N", "Insulatard"], "category": "antidiabetic_insulin", "dosage_forms": ["injection"], "strengths": ["100 IU/ml"]},
    {"generic_name": "Insulin Glargine", "brand_names": ["Lantus", "Basaglar"], "category": "antidiabetic_insulin", "dosage_forms": ["injection"], "strengths": ["100 IU/ml", "300 IU/ml"]},
    {"generic_name": "Insulin Aspart", "brand_names": ["NovoLog", "NovoRapid"], "category": "antidiabetic_insulin", "dosage_forms": ["injection"], "strengths": ["100 IU/ml"]},
    {"generic_name": "Sitagliptin", "brand_names": ["Januvia"], "category": "antidiabetic_dpp4_inhibitor", "dosage_forms": ["tablet"], "strengths": ["25mg", "50mg", "100mg"]},
    {"generic_name": "Empagliflozin", "brand_names": ["Jardiance"], "category": "antidiabetic_sglt2_inhibitor", "dosage_forms": ["tablet"], "strengths": ["10mg", "25mg"]},
    {"generic_name": "Pioglitazone", "brand_names": ["Actos"], "category": "antidiabetic_thiazolidinedione", "dosage_forms": ["tablet"], "strengths": ["15mg", "30mg", "45mg"]},
    
    # ==========================================
    # GASTROINTESTINAL
    # ==========================================
    {"generic_name": "Omeprazole", "brand_names": ["Prilosec", "Losec", "Omez"], "category": "gastrointestinal_ppi", "dosage_forms": ["capsule", "injection"], "strengths": ["10mg", "20mg", "40mg"]},
    {"generic_name": "Esomeprazole", "brand_names": ["Nexium"], "category": "gastrointestinal_ppi", "dosage_forms": ["capsule", "injection"], "strengths": ["20mg", "40mg"]},
    {"generic_name": "Pantoprazole", "brand_names": ["Protonix", "Pantoloc"], "category": "gastrointestinal_ppi", "dosage_forms": ["tablet", "injection"], "strengths": ["20mg", "40mg"]},
    {"generic_name": "Lansoprazole", "brand_names": ["Prevacid", "Zoton"], "category": "gastrointestinal_ppi", "dosage_forms": ["capsule"], "strengths": ["15mg", "30mg"]},
    {"generic_name": "Ranitidine", "brand_names": ["Zantac"], "category": "gastrointestinal_h2_blocker", "dosage_forms": ["tablet", "injection", "syrup"], "strengths": ["150mg", "300mg", "75mg/5ml"]},
    {"generic_name": "Famotidine", "brand_names": ["Pepcid"], "category": "gastrointestinal_h2_blocker", "dosage_forms": ["tablet", "injection"], "strengths": ["20mg", "40mg"]},
    {"generic_name": "Metoclopramide", "brand_names": ["Reglan", "Plasil", "Maxolon"], "category": "gastrointestinal_antiemetic", "dosage_forms": ["tablet", "injection", "syrup"], "strengths": ["10mg", "5mg/5ml"]},
    {"generic_name": "Domperidone", "brand_names": ["Motilium"], "category": "gastrointestinal_antiemetic", "dosage_forms": ["tablet", "suspension"], "strengths": ["10mg", "5mg/5ml"]},
    {"generic_name": "Ondansetron", "brand_names": ["Zofran"], "category": "gastrointestinal_antiemetic", "dosage_forms": ["tablet", "injection", "syrup"], "strengths": ["4mg", "8mg", "2mg/ml"]},
    {"generic_name": "Loperamide", "brand_names": ["Imodium"], "category": "gastrointestinal_antidiarrheal", "dosage_forms": ["capsule", "tablet"], "strengths": ["2mg"]},
    {"generic_name": "Oral Rehydration Salts", "brand_names": ["ORS", "Gastrolyte", "Pedialyte"], "category": "gastrointestinal_rehydration", "dosage_forms": ["powder"], "strengths": ["20.5g/sachet"]},
    {"generic_name": "Bisacodyl", "brand_names": ["Dulcolax"], "category": "gastrointestinal_laxative", "dosage_forms": ["tablet", "suppository"], "strengths": ["5mg", "10mg"]},
    {"generic_name": "Lactulose", "brand_names": ["Duphalac", "Kristalose"], "category": "gastrointestinal_laxative", "dosage_forms": ["syrup"], "strengths": ["10g/15ml"]},
    
    # ==========================================
    # ANTIHISTAMINES
    # ==========================================
    {"generic_name": "Cetirizine", "brand_names": ["Zyrtec", "Cetrizet"], "category": "antihistamine", "dosage_forms": ["tablet", "syrup"], "strengths": ["5mg", "10mg", "5mg/5ml"]},
    {"generic_name": "Loratadine", "brand_names": ["Claritin", "Alavert"], "category": "antihistamine", "dosage_forms": ["tablet", "syrup"], "strengths": ["10mg", "5mg/5ml"]},
    {"generic_name": "Chlorpheniramine", "brand_names": ["Piriton", "Chlor-Trimeton"], "category": "antihistamine", "dosage_forms": ["tablet", "syrup", "injection"], "strengths": ["4mg", "2mg/5ml"]},
    {"generic_name": "Diphenhydramine", "brand_names": ["Benadryl"], "category": "antihistamine", "dosage_forms": ["capsule", "syrup", "injection"], "strengths": ["25mg", "50mg", "12.5mg/5ml"]},
    {"generic_name": "Promethazine", "brand_names": ["Phenergan"], "category": "antihistamine", "dosage_forms": ["tablet", "injection", "syrup"], "strengths": ["10mg", "25mg", "5mg/5ml"]},
    {"generic_name": "Fexofenadine", "brand_names": ["Allegra", "Telfast"], "category": "antihistamine", "dosage_forms": ["tablet"], "strengths": ["60mg", "120mg", "180mg"]},
    {"generic_name": "Desloratadine", "brand_names": ["Clarinex", "Aerius"], "category": "antihistamine", "dosage_forms": ["tablet", "syrup"], "strengths": ["5mg", "0.5mg/ml"]},
    
    # ==========================================
    # RESPIRATORY
    # ==========================================
    {"generic_name": "Salbutamol", "brand_names": ["Ventolin", "ProAir", "Salamol"], "category": "respiratory_bronchodilator", "dosage_forms": ["inhaler", "nebulizer solution", "tablet", "syrup"], "strengths": ["100mcg/dose", "2.5mg/2.5ml", "2mg", "4mg"]},
    {"generic_name": "Beclomethasone", "brand_names": ["Qvar", "Beclovent", "Becotide"], "category": "respiratory_corticosteroid", "dosage_forms": ["inhaler", "nasal spray"], "strengths": ["50mcg", "100mcg", "250mcg"]},
    {"generic_name": "Budesonide", "brand_names": ["Pulmicort", "Rhinocort"], "category": "respiratory_corticosteroid", "dosage_forms": ["inhaler", "nebulizer", "nasal spray"], "strengths": ["100mcg", "200mcg", "400mcg", "0.25mg/ml", "0.5mg/ml"]},
    {"generic_name": "Fluticasone", "brand_names": ["Flixotide", "Flovent", "Flonase"], "category": "respiratory_corticosteroid", "dosage_forms": ["inhaler", "nasal spray"], "strengths": ["50mcg", "125mcg", "250mcg"]},
    {"generic_name": "Ipratropium", "brand_names": ["Atrovent"], "category": "respiratory_anticholinergic", "dosage_forms": ["inhaler", "nebulizer"], "strengths": ["20mcg/dose", "250mcg/ml"]},
    {"generic_name": "Montelukast", "brand_names": ["Singulair"], "category": "respiratory_leukotriene_antagonist", "dosage_forms": ["tablet", "chewable"], "strengths": ["4mg", "5mg", "10mg"]},
    {"generic_name": "Theophylline", "brand_names": ["Theo-Dur", "Uniphyl"], "category": "respiratory_xanthine", "dosage_forms": ["tablet", "capsule"], "strengths": ["100mg", "200mg", "300mg", "400mg"]},
    {"generic_name": "Aminophylline", "brand_names": ["Phyllocontin"], "category": "respiratory_xanthine", "dosage_forms": ["tablet", "injection"], "strengths": ["100mg", "225mg", "250mg/10ml"]},
    {"generic_name": "Fluticasone/Salmeterol", "brand_names": ["Advair", "Seretide"], "category": "respiratory_combination", "dosage_forms": ["inhaler"], "strengths": ["100/50mcg", "250/50mcg", "500/50mcg"]},
    {"generic_name": "Budesonide/Formoterol", "brand_names": ["Symbicort"], "category": "respiratory_combination", "dosage_forms": ["inhaler"], "strengths": ["80/4.5mcg", "160/4.5mcg", "320/9mcg"]},
    
    # ==========================================
    # CORTICOSTEROIDS (SYSTEMIC)
    # ==========================================
    {"generic_name": "Prednisolone", "brand_names": ["Prelone", "Orapred"], "category": "corticosteroid", "dosage_forms": ["tablet", "syrup", "injection"], "strengths": ["5mg", "15mg/5ml", "25mg/ml"]},
    {"generic_name": "Prednisone", "brand_names": ["Deltasone", "Rayos"], "category": "corticosteroid", "dosage_forms": ["tablet"], "strengths": ["1mg", "5mg", "10mg", "20mg", "50mg"]},
    {"generic_name": "Dexamethasone", "brand_names": ["Decadron"], "category": "corticosteroid", "dosage_forms": ["tablet", "injection"], "strengths": ["0.5mg", "4mg", "4mg/ml", "8mg/2ml"]},
    {"generic_name": "Hydrocortisone", "brand_names": ["Cortef", "Solu-Cortef"], "category": "corticosteroid", "dosage_forms": ["tablet", "injection", "cream"], "strengths": ["10mg", "20mg", "100mg", "1%"]},
    {"generic_name": "Methylprednisolone", "brand_names": ["Medrol", "Solu-Medrol"], "category": "corticosteroid", "dosage_forms": ["tablet", "injection"], "strengths": ["4mg", "16mg", "40mg", "125mg", "500mg", "1g"]},
    
    # ==========================================
    # ANTIFUNGALS
    # ==========================================
    {"generic_name": "Fluconazole", "brand_names": ["Diflucan", "Flucoral"], "category": "antifungal", "dosage_forms": ["capsule", "injection", "suspension"], "strengths": ["50mg", "100mg", "150mg", "200mg", "2mg/ml"]},
    {"generic_name": "Clotrimazole", "brand_names": ["Canesten", "Lotrimin"], "category": "antifungal", "dosage_forms": ["cream", "pessary", "solution"], "strengths": ["1%", "100mg", "200mg", "500mg"]},
    {"generic_name": "Miconazole", "brand_names": ["Daktarin", "Monistat"], "category": "antifungal", "dosage_forms": ["cream", "gel", "pessary"], "strengths": ["2%"]},
    {"generic_name": "Ketoconazole", "brand_names": ["Nizoral"], "category": "antifungal", "dosage_forms": ["tablet", "cream", "shampoo"], "strengths": ["200mg", "2%"]},
    {"generic_name": "Itraconazole", "brand_names": ["Sporanox"], "category": "antifungal", "dosage_forms": ["capsule", "solution"], "strengths": ["100mg", "10mg/ml"]},
    {"generic_name": "Nystatin", "brand_names": ["Mycostatin", "Nystan"], "category": "antifungal", "dosage_forms": ["suspension", "cream", "pessary"], "strengths": ["100,000 IU/ml", "100,000 IU/g"]},
    {"generic_name": "Terbinafine", "brand_names": ["Lamisil"], "category": "antifungal", "dosage_forms": ["tablet", "cream"], "strengths": ["250mg", "1%"]},
    {"generic_name": "Griseofulvin", "brand_names": ["Grifulvin", "Grisactin"], "category": "antifungal", "dosage_forms": ["tablet"], "strengths": ["250mg", "500mg"]},
    {"generic_name": "Amphotericin B", "brand_names": ["Fungizone", "AmBisome"], "category": "antifungal", "dosage_forms": ["injection"], "strengths": ["50mg"]},
    
    # ==========================================
    # ANTIVIRALS
    # ==========================================
    {"generic_name": "Acyclovir", "brand_names": ["Zovirax"], "category": "antiviral", "dosage_forms": ["tablet", "cream", "injection", "suspension"], "strengths": ["200mg", "400mg", "800mg", "5%", "250mg"]},
    {"generic_name": "Valacyclovir", "brand_names": ["Valtrex"], "category": "antiviral", "dosage_forms": ["tablet"], "strengths": ["500mg", "1000mg"]},
    {"generic_name": "Oseltamivir", "brand_names": ["Tamiflu"], "category": "antiviral", "dosage_forms": ["capsule", "suspension"], "strengths": ["30mg", "45mg", "75mg", "6mg/ml"]},
    {"generic_name": "Ribavirin", "brand_names": ["Rebetol", "Virazole"], "category": "antiviral", "dosage_forms": ["capsule", "tablet"], "strengths": ["200mg", "400mg", "600mg"]},
    {"generic_name": "Lamivudine", "brand_names": ["Epivir", "3TC"], "category": "antiviral_arv", "dosage_forms": ["tablet", "solution"], "strengths": ["100mg", "150mg", "300mg", "10mg/ml"]},
    {"generic_name": "Tenofovir", "brand_names": ["Viread"], "category": "antiviral_arv", "dosage_forms": ["tablet"], "strengths": ["300mg"]},
    {"generic_name": "Efavirenz", "brand_names": ["Sustiva", "Stocrin"], "category": "antiviral_arv", "dosage_forms": ["tablet", "capsule"], "strengths": ["200mg", "600mg"]},
    {"generic_name": "Zidovudine", "brand_names": ["Retrovir", "AZT"], "category": "antiviral_arv", "dosage_forms": ["capsule", "syrup", "injection"], "strengths": ["100mg", "250mg", "300mg", "10mg/ml"]},
    {"generic_name": "Nevirapine", "brand_names": ["Viramune"], "category": "antiviral_arv", "dosage_forms": ["tablet", "suspension"], "strengths": ["200mg", "50mg/5ml"]},
    {"generic_name": "Atazanavir", "brand_names": ["Reyataz"], "category": "antiviral_arv", "dosage_forms": ["capsule"], "strengths": ["150mg", "200mg", "300mg"]},
    {"generic_name": "Lopinavir/Ritonavir", "brand_names": ["Kaletra", "Aluvia"], "category": "antiviral_arv", "dosage_forms": ["tablet", "solution"], "strengths": ["200/50mg", "100/25mg", "80/20mg/ml"]},
    {"generic_name": "Dolutegravir", "brand_names": ["Tivicay"], "category": "antiviral_arv", "dosage_forms": ["tablet"], "strengths": ["50mg"]},
    
    # ==========================================
    # VITAMINS & SUPPLEMENTS
    # ==========================================
    {"generic_name": "Multivitamin", "brand_names": ["Centrum", "One-A-Day", "Vitabiotics"], "category": "vitamin", "dosage_forms": ["tablet", "capsule", "syrup"], "strengths": ["various"]},
    {"generic_name": "Vitamin A", "brand_names": ["Aquasol A", "Retinol"], "category": "vitamin", "dosage_forms": ["capsule", "injection"], "strengths": ["25,000 IU", "50,000 IU", "100,000 IU", "200,000 IU"]},
    {"generic_name": "Vitamin B Complex", "brand_names": ["B-Complex", "Neurobion"], "category": "vitamin", "dosage_forms": ["tablet", "injection"], "strengths": ["various"]},
    {"generic_name": "Vitamin B12", "brand_names": ["Cyanocobalamin"], "category": "vitamin", "dosage_forms": ["tablet", "injection"], "strengths": ["250mcg", "500mcg", "1000mcg"]},
    {"generic_name": "Vitamin C", "brand_names": ["Ascorbic Acid", "Celin", "Redoxon"], "category": "vitamin", "dosage_forms": ["tablet", "injection", "effervescent"], "strengths": ["100mg", "250mg", "500mg", "1000mg"]},
    {"generic_name": "Vitamin D3", "brand_names": ["Cholecalciferol", "D-Drops"], "category": "vitamin", "dosage_forms": ["tablet", "capsule", "drops"], "strengths": ["400 IU", "1000 IU", "2000 IU", "5000 IU", "50,000 IU"]},
    {"generic_name": "Vitamin E", "brand_names": ["Evion", "Alpha-Tocopherol"], "category": "vitamin", "dosage_forms": ["capsule"], "strengths": ["100 IU", "200 IU", "400 IU"]},
    {"generic_name": "Folic Acid", "brand_names": ["Folate", "Folvite"], "category": "vitamin", "dosage_forms": ["tablet"], "strengths": ["0.4mg", "1mg", "5mg"]},
    {"generic_name": "Iron (Ferrous Sulfate)", "brand_names": ["Feosol", "Fer-In-Sol", "Ferograd"], "category": "mineral", "dosage_forms": ["tablet", "syrup", "drops"], "strengths": ["200mg", "300mg", "325mg", "125mg/5ml"]},
    {"generic_name": "Iron (Ferrous Fumarate)", "brand_names": ["Femiron", "Palafer"], "category": "mineral", "dosage_forms": ["tablet", "capsule"], "strengths": ["200mg", "300mg"]},
    {"generic_name": "Calcium + Vitamin D", "brand_names": ["Caltrate", "Os-Cal", "Calcichew D3"], "category": "mineral", "dosage_forms": ["tablet", "chewable"], "strengths": ["500mg+200IU", "600mg+400IU", "1000mg+800IU"]},
    {"generic_name": "Zinc", "brand_names": ["Zinc Sulfate", "Zincovit"], "category": "mineral", "dosage_forms": ["tablet", "syrup"], "strengths": ["10mg", "20mg", "50mg"]},
    {"generic_name": "Magnesium", "brand_names": ["Mag-Ox", "Slow-Mag"], "category": "mineral", "dosage_forms": ["tablet"], "strengths": ["250mg", "400mg", "500mg"]},
    {"generic_name": "Potassium Chloride", "brand_names": ["K-Dur", "Slow-K"], "category": "mineral", "dosage_forms": ["tablet", "solution"], "strengths": ["600mg", "750mg", "10mEq/15ml"]},
    
    # ==========================================
    # DERMATOLOGICAL
    # ==========================================
    {"generic_name": "Betamethasone", "brand_names": ["Betnovate", "Diprosone", "Celestone"], "category": "dermatological_corticosteroid", "dosage_forms": ["cream", "ointment", "lotion"], "strengths": ["0.025%", "0.05%", "0.1%"]},
    {"generic_name": "Hydrocortisone", "brand_names": ["Cortaid", "Dermacort"], "category": "dermatological_corticosteroid", "dosage_forms": ["cream", "ointment"], "strengths": ["0.5%", "1%", "2.5%"]},
    {"generic_name": "Mometasone", "brand_names": ["Elocon"], "category": "dermatological_corticosteroid", "dosage_forms": ["cream", "ointment", "lotion"], "strengths": ["0.1%"]},
    {"generic_name": "Clobetasol", "brand_names": ["Dermovate", "Temovate"], "category": "dermatological_corticosteroid", "dosage_forms": ["cream", "ointment"], "strengths": ["0.05%"]},
    {"generic_name": "Benzoyl Peroxide", "brand_names": ["Benzac", "PanOxyl"], "category": "dermatological_acne", "dosage_forms": ["gel", "wash"], "strengths": ["2.5%", "5%", "10%"]},
    {"generic_name": "Tretinoin", "brand_names": ["Retin-A", "Renova"], "category": "dermatological_retinoid", "dosage_forms": ["cream", "gel"], "strengths": ["0.025%", "0.05%", "0.1%"]},
    {"generic_name": "Adapalene", "brand_names": ["Differin"], "category": "dermatological_retinoid", "dosage_forms": ["gel", "cream"], "strengths": ["0.1%", "0.3%"]},
    {"generic_name": "Permethrin", "brand_names": ["Elimite", "Nix"], "category": "dermatological_antiparasitic", "dosage_forms": ["cream", "lotion"], "strengths": ["1%", "5%"]},
    {"generic_name": "Silver Sulfadiazine", "brand_names": ["Silvadene", "Flamazine"], "category": "dermatological_antibacterial", "dosage_forms": ["cream"], "strengths": ["1%"]},
    {"generic_name": "Mupirocin", "brand_names": ["Bactroban"], "category": "dermatological_antibacterial", "dosage_forms": ["ointment", "cream"], "strengths": ["2%"]},
    {"generic_name": "Fusidic Acid", "brand_names": ["Fucidin"], "category": "dermatological_antibacterial", "dosage_forms": ["cream", "ointment"], "strengths": ["2%"]},
    {"generic_name": "Calamine Lotion", "brand_names": ["Calamine", "Caladryl"], "category": "dermatological_antipruritic", "dosage_forms": ["lotion"], "strengths": ["8%"]},
    
    # ==========================================
    # OPHTHALMIC
    # ==========================================
    {"generic_name": "Chloramphenicol Eye Drops", "brand_names": ["Chloromycetin"], "category": "ophthalmic_antibiotic", "dosage_forms": ["drops", "ointment"], "strengths": ["0.5%", "1%"]},
    {"generic_name": "Tobramycin Eye Drops", "brand_names": ["Tobrex"], "category": "ophthalmic_antibiotic", "dosage_forms": ["drops", "ointment"], "strengths": ["0.3%"]},
    {"generic_name": "Ciprofloxacin Eye Drops", "brand_names": ["Ciloxan"], "category": "ophthalmic_antibiotic", "dosage_forms": ["drops"], "strengths": ["0.3%"]},
    {"generic_name": "Dexamethasone Eye Drops", "brand_names": ["Maxidex"], "category": "ophthalmic_corticosteroid", "dosage_forms": ["drops"], "strengths": ["0.1%"]},
    {"generic_name": "Prednisolone Eye Drops", "brand_names": ["Pred Forte"], "category": "ophthalmic_corticosteroid", "dosage_forms": ["drops"], "strengths": ["1%"]},
    {"generic_name": "Timolol Eye Drops", "brand_names": ["Timoptic"], "category": "ophthalmic_glaucoma", "dosage_forms": ["drops"], "strengths": ["0.25%", "0.5%"]},
    {"generic_name": "Latanoprost Eye Drops", "brand_names": ["Xalatan"], "category": "ophthalmic_glaucoma", "dosage_forms": ["drops"], "strengths": ["0.005%"]},
    {"generic_name": "Artificial Tears", "brand_names": ["Systane", "Refresh", "Tears Naturale"], "category": "ophthalmic_lubricant", "dosage_forms": ["drops"], "strengths": ["various"]},
    {"generic_name": "Atropine Eye Drops", "brand_names": ["Isopto Atropine"], "category": "ophthalmic_mydriatic", "dosage_forms": ["drops"], "strengths": ["0.5%", "1%"]},
    {"generic_name": "Tropicamide Eye Drops", "brand_names": ["Mydriacyl"], "category": "ophthalmic_mydriatic", "dosage_forms": ["drops"], "strengths": ["0.5%", "1%"]},
    
    # ==========================================
    # PSYCHIATRIC/NEUROLOGICAL
    # ==========================================
    {"generic_name": "Amitriptyline", "brand_names": ["Elavil", "Endep"], "category": "psychiatric_antidepressant", "dosage_forms": ["tablet"], "strengths": ["10mg", "25mg", "50mg", "75mg"]},
    {"generic_name": "Fluoxetine", "brand_names": ["Prozac"], "category": "psychiatric_ssri", "dosage_forms": ["capsule", "tablet"], "strengths": ["10mg", "20mg", "40mg"]},
    {"generic_name": "Sertraline", "brand_names": ["Zoloft"], "category": "psychiatric_ssri", "dosage_forms": ["tablet"], "strengths": ["25mg", "50mg", "100mg"]},
    {"generic_name": "Escitalopram", "brand_names": ["Lexapro", "Cipralex"], "category": "psychiatric_ssri", "dosage_forms": ["tablet"], "strengths": ["5mg", "10mg", "20mg"]},
    {"generic_name": "Diazepam", "brand_names": ["Valium"], "category": "psychiatric_benzodiazepine", "dosage_forms": ["tablet", "injection"], "strengths": ["2mg", "5mg", "10mg", "5mg/ml"]},
    {"generic_name": "Lorazepam", "brand_names": ["Ativan"], "category": "psychiatric_benzodiazepine", "dosage_forms": ["tablet", "injection"], "strengths": ["0.5mg", "1mg", "2mg", "4mg/ml"]},
    {"generic_name": "Alprazolam", "brand_names": ["Xanax"], "category": "psychiatric_benzodiazepine", "dosage_forms": ["tablet"], "strengths": ["0.25mg", "0.5mg", "1mg", "2mg"]},
    {"generic_name": "Haloperidol", "brand_names": ["Haldol"], "category": "psychiatric_antipsychotic", "dosage_forms": ["tablet", "injection"], "strengths": ["0.5mg", "1mg", "2mg", "5mg", "5mg/ml"]},
    {"generic_name": "Risperidone", "brand_names": ["Risperdal"], "category": "psychiatric_antipsychotic", "dosage_forms": ["tablet", "solution"], "strengths": ["0.25mg", "0.5mg", "1mg", "2mg", "3mg", "4mg"]},
    {"generic_name": "Olanzapine", "brand_names": ["Zyprexa"], "category": "psychiatric_antipsychotic", "dosage_forms": ["tablet", "injection"], "strengths": ["2.5mg", "5mg", "7.5mg", "10mg", "15mg", "20mg"]},
    {"generic_name": "Quetiapine", "brand_names": ["Seroquel"], "category": "psychiatric_antipsychotic", "dosage_forms": ["tablet"], "strengths": ["25mg", "100mg", "200mg", "300mg"]},
    {"generic_name": "Carbamazepine", "brand_names": ["Tegretol"], "category": "neurological_anticonvulsant", "dosage_forms": ["tablet", "suspension"], "strengths": ["100mg", "200mg", "400mg", "100mg/5ml"]},
    {"generic_name": "Phenytoin", "brand_names": ["Dilantin", "Epanutin"], "category": "neurological_anticonvulsant", "dosage_forms": ["capsule", "injection", "suspension"], "strengths": ["25mg", "50mg", "100mg", "50mg/ml"]},
    {"generic_name": "Valproic Acid", "brand_names": ["Depakote", "Epilim"], "category": "neurological_anticonvulsant", "dosage_forms": ["tablet", "syrup"], "strengths": ["200mg", "500mg", "200mg/5ml"]},
    {"generic_name": "Levetiracetam", "brand_names": ["Keppra"], "category": "neurological_anticonvulsant", "dosage_forms": ["tablet", "solution", "injection"], "strengths": ["250mg", "500mg", "750mg", "1000mg"]},
    {"generic_name": "Phenobarbital", "brand_names": ["Luminal"], "category": "neurological_anticonvulsant", "dosage_forms": ["tablet", "injection", "elixir"], "strengths": ["15mg", "30mg", "60mg", "100mg"]},
    {"generic_name": "Gabapentin", "brand_names": ["Neurontin"], "category": "neurological_anticonvulsant", "dosage_forms": ["capsule", "tablet"], "strengths": ["100mg", "300mg", "400mg", "600mg", "800mg"]},
    {"generic_name": "Pregabalin", "brand_names": ["Lyrica"], "category": "neurological_anticonvulsant", "dosage_forms": ["capsule"], "strengths": ["25mg", "50mg", "75mg", "100mg", "150mg", "200mg", "300mg"]},
    
    # ==========================================
    # CARDIOVASCULAR - LIPID LOWERING
    # ==========================================
    {"generic_name": "Atorvastatin", "brand_names": ["Lipitor"], "category": "cardiovascular_statin", "dosage_forms": ["tablet"], "strengths": ["10mg", "20mg", "40mg", "80mg"]},
    {"generic_name": "Simvastatin", "brand_names": ["Zocor"], "category": "cardiovascular_statin", "dosage_forms": ["tablet"], "strengths": ["5mg", "10mg", "20mg", "40mg", "80mg"]},
    {"generic_name": "Rosuvastatin", "brand_names": ["Crestor"], "category": "cardiovascular_statin", "dosage_forms": ["tablet"], "strengths": ["5mg", "10mg", "20mg", "40mg"]},
    {"generic_name": "Pravastatin", "brand_names": ["Pravachol"], "category": "cardiovascular_statin", "dosage_forms": ["tablet"], "strengths": ["10mg", "20mg", "40mg", "80mg"]},
    {"generic_name": "Fenofibrate", "brand_names": ["Tricor", "Lipanthyl"], "category": "cardiovascular_fibrate", "dosage_forms": ["capsule", "tablet"], "strengths": ["67mg", "134mg", "200mg"]},
    {"generic_name": "Ezetimibe", "brand_names": ["Zetia"], "category": "cardiovascular_cholesterol_absorption_inhibitor", "dosage_forms": ["tablet"], "strengths": ["10mg"]},
    
    # ==========================================
    # CARDIOVASCULAR - ANTICOAGULANTS & ANTIPLATELETS
    # ==========================================
    {"generic_name": "Warfarin", "brand_names": ["Coumadin", "Jantoven"], "category": "cardiovascular_anticoagulant", "dosage_forms": ["tablet"], "strengths": ["1mg", "2mg", "2.5mg", "3mg", "4mg", "5mg", "7.5mg", "10mg"]},
    {"generic_name": "Heparin", "brand_names": ["Heparin Sodium"], "category": "cardiovascular_anticoagulant", "dosage_forms": ["injection"], "strengths": ["1000 IU/ml", "5000 IU/ml", "25000 IU/5ml"]},
    {"generic_name": "Enoxaparin", "brand_names": ["Lovenox", "Clexane"], "category": "cardiovascular_anticoagulant", "dosage_forms": ["injection"], "strengths": ["20mg", "40mg", "60mg", "80mg", "100mg", "120mg", "150mg"]},
    {"generic_name": "Rivaroxaban", "brand_names": ["Xarelto"], "category": "cardiovascular_anticoagulant", "dosage_forms": ["tablet"], "strengths": ["10mg", "15mg", "20mg"]},
    {"generic_name": "Apixaban", "brand_names": ["Eliquis"], "category": "cardiovascular_anticoagulant", "dosage_forms": ["tablet"], "strengths": ["2.5mg", "5mg"]},
    {"generic_name": "Clopidogrel", "brand_names": ["Plavix"], "category": "cardiovascular_antiplatelet", "dosage_forms": ["tablet"], "strengths": ["75mg", "300mg"]},
    {"generic_name": "Ticagrelor", "brand_names": ["Brilinta"], "category": "cardiovascular_antiplatelet", "dosage_forms": ["tablet"], "strengths": ["60mg", "90mg"]},
    
    # ==========================================
    # CARDIOVASCULAR - OTHER
    # ==========================================
    {"generic_name": "Digoxin", "brand_names": ["Lanoxin"], "category": "cardiovascular_cardiac_glycoside", "dosage_forms": ["tablet", "injection", "elixir"], "strengths": ["0.0625mg", "0.125mg", "0.25mg", "0.5mg/2ml"]},
    {"generic_name": "Amiodarone", "brand_names": ["Cordarone", "Pacerone"], "category": "cardiovascular_antiarrhythmic", "dosage_forms": ["tablet", "injection"], "strengths": ["100mg", "200mg", "150mg/3ml"]},
    {"generic_name": "Isosorbide Dinitrate", "brand_names": ["Isordil", "Sorbitrate"], "category": "cardiovascular_nitrate", "dosage_forms": ["tablet", "sublingual"], "strengths": ["5mg", "10mg", "20mg", "40mg"]},
    {"generic_name": "Isosorbide Mononitrate", "brand_names": ["Imdur", "Monoket"], "category": "cardiovascular_nitrate", "dosage_forms": ["tablet"], "strengths": ["20mg", "30mg", "60mg", "120mg"]},
    {"generic_name": "Nitroglycerin", "brand_names": ["Nitrostat", "Nitrolingual"], "category": "cardiovascular_nitrate", "dosage_forms": ["sublingual tablet", "spray", "patch"], "strengths": ["0.3mg", "0.4mg", "0.6mg", "0.4mg/spray"]},
    {"generic_name": "Dopamine", "brand_names": ["Intropin"], "category": "cardiovascular_inotrope", "dosage_forms": ["injection"], "strengths": ["40mg/ml", "80mg/ml", "200mg/5ml"]},
    {"generic_name": "Dobutamine", "brand_names": ["Dobutrex"], "category": "cardiovascular_inotrope", "dosage_forms": ["injection"], "strengths": ["250mg/20ml"]},
    {"generic_name": "Epinephrine/Adrenaline", "brand_names": ["EpiPen", "Adrenalin"], "category": "cardiovascular_vasopressor", "dosage_forms": ["injection", "auto-injector"], "strengths": ["1mg/ml", "0.3mg", "0.15mg"]},
    {"generic_name": "Norepinephrine", "brand_names": ["Levophed"], "category": "cardiovascular_vasopressor", "dosage_forms": ["injection"], "strengths": ["1mg/ml", "4mg/4ml"]},
    
    # ==========================================
    # HORMONES & CONTRACEPTIVES
    # ==========================================
    {"generic_name": "Levothyroxine", "brand_names": ["Synthroid", "Levoxyl", "Euthyrox"], "category": "hormone_thyroid", "dosage_forms": ["tablet"], "strengths": ["25mcg", "50mcg", "75mcg", "100mcg", "125mcg", "150mcg", "200mcg"]},
    {"generic_name": "Carbimazole", "brand_names": ["Neo-Mercazole"], "category": "hormone_antithyroid", "dosage_forms": ["tablet"], "strengths": ["5mg", "20mg"]},
    {"generic_name": "Propylthiouracil", "brand_names": ["PTU"], "category": "hormone_antithyroid", "dosage_forms": ["tablet"], "strengths": ["50mg"]},
    {"generic_name": "Ethinylestradiol/Levonorgestrel", "brand_names": ["Microgynon", "Alesse", "Levlen"], "category": "contraceptive_oral", "dosage_forms": ["tablet"], "strengths": ["30/150mcg", "20/100mcg"]},
    {"generic_name": "Ethinylestradiol/Norgestrel", "brand_names": ["Lo/Ovral", "Cryselle"], "category": "contraceptive_oral", "dosage_forms": ["tablet"], "strengths": ["30/300mcg"]},
    {"generic_name": "Levonorgestrel", "brand_names": ["Plan B", "Postinor"], "category": "contraceptive_emergency", "dosage_forms": ["tablet"], "strengths": ["0.75mg", "1.5mg"]},
    {"generic_name": "Medroxyprogesterone", "brand_names": ["Depo-Provera", "Provera"], "category": "contraceptive_injectable", "dosage_forms": ["injection", "tablet"], "strengths": ["150mg/ml", "2.5mg", "5mg", "10mg"]},
    {"generic_name": "Norethisterone", "brand_names": ["Noristerat", "Primolut N"], "category": "hormone_progestogen", "dosage_forms": ["tablet", "injection"], "strengths": ["5mg", "200mg/ml"]},
    {"generic_name": "Conjugated Estrogens", "brand_names": ["Premarin"], "category": "hormone_estrogen", "dosage_forms": ["tablet", "cream"], "strengths": ["0.3mg", "0.625mg", "1.25mg"]},
    {"generic_name": "Testosterone", "brand_names": ["Depo-Testosterone", "AndroGel"], "category": "hormone_androgen", "dosage_forms": ["injection", "gel"], "strengths": ["100mg/ml", "200mg/ml", "1%"]},
    {"generic_name": "Oxytocin", "brand_names": ["Pitocin", "Syntocinon"], "category": "hormone_uterotonic", "dosage_forms": ["injection"], "strengths": ["10 IU/ml"]},
    {"generic_name": "Ergometrine", "brand_names": ["Ergotrate", "Ergonovine"], "category": "hormone_uterotonic", "dosage_forms": ["injection", "tablet"], "strengths": ["0.2mg/ml", "0.2mg"]},
    {"generic_name": "Misoprostol", "brand_names": ["Cytotec"], "category": "hormone_prostaglandin", "dosage_forms": ["tablet"], "strengths": ["200mcg"]},
    
    # ==========================================
    # ANESTHETICS & MUSCLE RELAXANTS
    # ==========================================
    {"generic_name": "Lidocaine", "brand_names": ["Xylocaine", "Lignocaine"], "category": "anesthetic_local", "dosage_forms": ["injection", "gel", "spray"], "strengths": ["1%", "2%", "4%", "10%"]},
    {"generic_name": "Bupivacaine", "brand_names": ["Marcaine", "Sensorcaine"], "category": "anesthetic_local", "dosage_forms": ["injection"], "strengths": ["0.25%", "0.5%", "0.75%"]},
    {"generic_name": "Ketamine", "brand_names": ["Ketalar"], "category": "anesthetic_general", "dosage_forms": ["injection"], "strengths": ["10mg/ml", "50mg/ml", "100mg/ml"]},
    {"generic_name": "Propofol", "brand_names": ["Diprivan"], "category": "anesthetic_general", "dosage_forms": ["injection"], "strengths": ["10mg/ml"]},
    {"generic_name": "Thiopental", "brand_names": ["Pentothal"], "category": "anesthetic_general", "dosage_forms": ["injection"], "strengths": ["500mg", "1g"]},
    {"generic_name": "Succinylcholine", "brand_names": ["Anectine", "Quelicin"], "category": "muscle_relaxant_neuromuscular", "dosage_forms": ["injection"], "strengths": ["20mg/ml"]},
    {"generic_name": "Atracurium", "brand_names": ["Tracrium"], "category": "muscle_relaxant_neuromuscular", "dosage_forms": ["injection"], "strengths": ["10mg/ml"]},
    {"generic_name": "Vecuronium", "brand_names": ["Norcuron"], "category": "muscle_relaxant_neuromuscular", "dosage_forms": ["injection"], "strengths": ["10mg"]},
    {"generic_name": "Neostigmine", "brand_names": ["Prostigmin"], "category": "cholinesterase_inhibitor", "dosage_forms": ["injection", "tablet"], "strengths": ["0.5mg/ml", "2.5mg/ml", "15mg"]},
    {"generic_name": "Baclofen", "brand_names": ["Lioresal"], "category": "muscle_relaxant_skeletal", "dosage_forms": ["tablet"], "strengths": ["10mg", "25mg"]},
    {"generic_name": "Tizanidine", "brand_names": ["Zanaflex"], "category": "muscle_relaxant_skeletal", "dosage_forms": ["tablet", "capsule"], "strengths": ["2mg", "4mg"]},
    {"generic_name": "Cyclobenzaprine", "brand_names": ["Flexeril"], "category": "muscle_relaxant_skeletal", "dosage_forms": ["tablet"], "strengths": ["5mg", "10mg"]},
    
    # ==========================================
    # ANTIPARASITICS
    # ==========================================
    {"generic_name": "Albendazole", "brand_names": ["Albenza", "Zentel"], "category": "antiparasitic_antihelminth", "dosage_forms": ["tablet", "suspension"], "strengths": ["200mg", "400mg", "200mg/5ml"]},
    {"generic_name": "Mebendazole", "brand_names": ["Vermox"], "category": "antiparasitic_antihelminth", "dosage_forms": ["tablet", "suspension"], "strengths": ["100mg", "500mg", "100mg/5ml"]},
    {"generic_name": "Ivermectin", "brand_names": ["Stromectol", "Mectizan"], "category": "antiparasitic_antihelminth", "dosage_forms": ["tablet"], "strengths": ["3mg", "6mg"]},
    {"generic_name": "Praziquantel", "brand_names": ["Biltricide"], "category": "antiparasitic_antihelminth", "dosage_forms": ["tablet"], "strengths": ["600mg"]},
    {"generic_name": "Tinidazole", "brand_names": ["Tindamax", "Fasigyn"], "category": "antiparasitic_antiprotozoal", "dosage_forms": ["tablet"], "strengths": ["500mg"]},
    {"generic_name": "Secnidazole", "brand_names": ["Flagentyl", "Secnil"], "category": "antiparasitic_antiprotozoal", "dosage_forms": ["tablet"], "strengths": ["500mg", "1000mg"]},
    {"generic_name": "Niclosamide", "brand_names": ["Niclocide", "Yomesan"], "category": "antiparasitic_antihelminth", "dosage_forms": ["tablet"], "strengths": ["500mg"]},
    {"generic_name": "Diethylcarbamazine", "brand_names": ["Hetrazan"], "category": "antiparasitic_antifilarial", "dosage_forms": ["tablet"], "strengths": ["50mg", "100mg"]},
    
    # ==========================================
    # ANTITUBERCULAR
    # ==========================================
    {"generic_name": "Isoniazid", "brand_names": ["INH", "Nydrazid"], "category": "antitubercular", "dosage_forms": ["tablet", "syrup", "injection"], "strengths": ["100mg", "300mg", "50mg/5ml"]},
    {"generic_name": "Rifampicin", "brand_names": ["Rifadin", "Rimactane"], "category": "antitubercular", "dosage_forms": ["capsule", "suspension", "injection"], "strengths": ["150mg", "300mg", "450mg", "600mg", "100mg/5ml"]},
    {"generic_name": "Pyrazinamide", "brand_names": ["PZA", "Tebrazid"], "category": "antitubercular", "dosage_forms": ["tablet"], "strengths": ["400mg", "500mg"]},
    {"generic_name": "Ethambutol", "brand_names": ["Myambutol"], "category": "antitubercular", "dosage_forms": ["tablet"], "strengths": ["100mg", "400mg"]},
    {"generic_name": "Streptomycin", "brand_names": ["Streptomycin Sulfate"], "category": "antitubercular", "dosage_forms": ["injection"], "strengths": ["1g"]},
    {"generic_name": "RHZE (Fixed-Dose Combination)", "brand_names": ["Rifater", "Akurit-4"], "category": "antitubercular_fdc", "dosage_forms": ["tablet"], "strengths": ["150/75/400/275mg"]},
    {"generic_name": "RH (Fixed-Dose Combination)", "brand_names": ["Rifinah", "Rimactazid"], "category": "antitubercular_fdc", "dosage_forms": ["tablet"], "strengths": ["150/75mg", "300/150mg"]},
]

def get_all_medications():
    """Return all medications in the database"""
    return GLOBAL_MEDICATIONS

def search_medications(query: str, category: str = None, limit: int = 50):
    """Search medications by name or category"""
    results = []
    query_lower = query.lower() if query else ""
    
    for med in GLOBAL_MEDICATIONS:
        match = False
        
        if query_lower:
            if query_lower in med["generic_name"].lower():
                match = True
            elif any(query_lower in brand.lower() for brand in med.get("brand_names", [])):
                match = True
        else:
            match = True
        
        if category and med.get("category") != category:
            match = False
        
        if match:
            results.append(med)
            if len(results) >= limit:
                break
    
    return results

def get_medication_categories():
    """Get all unique medication categories"""
    categories = set()
    for med in GLOBAL_MEDICATIONS:
        categories.add(med.get("category", "uncategorized"))
    return sorted(list(categories))

def get_medications_by_category(category: str):
    """Get all medications in a specific category"""
    return [med for med in GLOBAL_MEDICATIONS if med.get("category") == category]
