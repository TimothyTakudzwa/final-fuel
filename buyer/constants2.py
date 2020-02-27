INDUSTRY_CHOICES = (("Accounting", "Accounting"),
                    ("Airlines / Aviation", "Airlines / Aviation"),
                    ("Alternative Dispute Resolution", "Alternative Dispute Resolution"),
                    ("Alternative Medicine", "Alternative Medicine"),
                    ("Animation", "Animation"),
                    ("Apparel / Fashion", "Apparel / Fashion"),
                    ("Architecture / Planning", "Architecture / Planning"),
                    ("Arts / Crafts", "Arts / Crafts"),
                    ("Automotive", "Automotive"),
                    ("Aviation / Aerospace", "Aviation / Aerospace"),
                    ("Banking / Mortgage", "Banking / Mortgage"),
                    ("Biotechnology / Greentech", "Biotechnology / Greentech"),
                    ("Broadcast Media", "Broadcast Media"),
                    ("Building Materials", "Building Materials"),
                    ("Business Supplies / Equipment", "Business Supplies / Equipment"),
                    ("Capital Markets / Hedge Fund / Private Equity", "Capital Markets / Hedge Fund / Private Equity"),
                    ("Chemicals", "Chemicals"),
                    ("Civic / Social Organization", "Civic / Social Organization"),
                    ("Civil Engineering", "Civil Engineering"),
                    ("Commercial Real Estate", "Commercial Real Estate"),
                    ("Computer Games", "Computer Games"),
                    ("Computer Hardware", "Computer Hardware"),
                    ("Computer Networking", "Computer Networking"),
                    ("Computer Software / Engineering", "Computer Software / Engineering"),
                    ("Computer / Network Security", "Computer / Network Security"),
                    ("Construction", "Construction"),
                    ("Consumer Electronics", "Consumer Electronics"),
                    ("Consumer Goods", "Consumer Goods"),
                    ("Consumer Services", "Consumer Services"),
                    ("Cosmetics", "Cosmetics"),
                    ("Dairy", "Dairy"),
                    ("Defense / Space", "Defense / Space"),
                    ("Design", "Design"),
                    ("E - Learning", "E - Learning"),
                    ("Education Management", "Education Management"),
                    ("Electrical / Electronic Manufacturing", "Electrical / Electronic Manufacturing"),
                    ("Entertainment / Movie Production", "Entertainment / Movie Production"),
                    ("Environmental Services", "Environmental Services"),
                    ("Events Services", "Events Services"),
                    ("Executive Office", "Executive Office"),
                    ("Facilities Services", "Facilities Services"),
                    ("Farming", "Farming"),
                    ("Financial Services", "Financial Services"),
                    ("Fine Art", "Fine Art"),
                    ("Fishery", "Fishery"),
                    ("Food Production", "Food Production"),
                    ("Food / Beverages", "Food / Beverages"),
                    ("Fundraising", "Fundraising"),
                    ("Furniture", "Furniture"),
                    ("Gambling / Casinos", "Gambling / Casinos"),
                    ("Glass / Ceramics / Concrete", "Glass / Ceramics / Concrete"),
                    ("Government Administration", "Government Administration"),
                    ("Government Relations", "Government Relations"),
                    ("Graphic Design / Web Design", "Graphic Design / Web Design"),
                    ("Health / Fitness", "Health / Fitness"),
                    ("Higher Education / Acadamia", "Higher Education / Acadamia"),
                    ("Hospital / Health Care", "Hospital / Health Care"),
                    ("Hospitality", "Hospitality"),
                    ("Human Resources / HR", "Human Resources / HR"),
                    ("Import / Export", "Import / Export"),
                    ("Individual / Family Services", "Individual / Family Services"),
                    ("Industrial Automation", "Industrial Automation"),
                    ("Information Services", "Information Services"),
                    ("Information Technology / IT", "Information Technology / IT"),
                    ("Insurance", "Insurance"),
                    ("International Affairs", "International Affairs"),
                    ("International Trade / Development", "International Trade / Development"),
                    ("Internet", "Internet"),
                    ("Investment Banking / Venture", "Investment Banking / Venture"),
                    ("Investment Management / Hedge Fund / Private Equity",
                     "Investment Management / Hedge Fund / Private Equity"),
                    ("Judiciary", "Judiciary"),
                    ("Law Enforcement", "Law Enforcement"),
                    ("Law Practice / Law Firms", "Law Practice / Law Firms"),
                    ("Legal Services", "Legal Services"),
                    ("Legislative Office", "Legislative Office"),
                    ("Leisure / Travel", "Leisure / Travel"),
                    ("Library", "Library"),
                    ("Logistics / Procurement", "Logistics / Procurement"),
                    ("Luxury Goods / Jewelry", "Luxury Goods / Jewelry"),
                    ("Machinery", "Machinery"),
                    ("Market Research", "Market Research"),
                    ("Marketing / Advertising / Sales", "Marketing / Advertising / Sales"),
                    ("Mechanical or Industrial Engineering", "Mechanical or Industrial Engineering"),
                    ("Media Production", "Media Production"),
                    ("Medical ", "Medical "),
                    ("Military Industry", "Military Industry"),
                    ("Mining / Metals", "Mining / Metals"),
                    ("Music", "Music"),
                    ("Newspapers / Journalism", "Newspapers / Journalism"),
                    ("Non - Profit / Volunteering", "Non - Profit / Volunteering"),
                    ("Oil / Energy / Solar / Greentech", "Oil / Energy / Solar / Greentech"),
                    ("Other Industry", "Other Industry"),
                    ("Pharmaceuticals", "Pharmaceuticals"),
                    ("Political Organization", "Political Organization"),
                    ("Primary / Secondary Education", "Primary / Secondary Education"),
                    ("Printing", "Printing"),
                    ("Real Estate / Mortgage", "Real Estate / Mortgage"),
                    ("Restaurants", "Restaurants"),
                    ("Retail Industry", "Retail Industry"),
                    ("Sports", "Sports"),
                    ("Telecommunications", "Telecommunications"),
                    ("Transportation", "Transportation"))
TYPE_CHOICES = (
    ('INDIVIDUAL', 'Individual'),
    ('S_ADMIN', 'Supplier Admin'),
    ('BUYER', 'Buyer'),
    ('SUPPLIER', 'Supplier'),
    ('SS_SUPPLIER', 'Service Station Rep'),
    ('ZERA', 'ZERA'),

)

COMPANY_CHOICES = (('CORPORATE', 'CORPORATE'), ('SUPPLIER', 'SUPPLIER'), ('TRANSPORTER', 'TRANSPORTER'))

SUPPLIER_CHOICES = (
    ('Admin', 'ADMIN'),
    ('Staff', 'STAFF'),
)

STORAGE_TANKS = (('ABOVE GROUND', 'ABOVE GROUND'), ('BELOW GROUND', 'BELOW GROUND'))
job_titles = [
    "accountant",
    "actor",
    "actuary",
    "adhesive bonding machine tender",
    "adjudicator",
    "administrative assistant",
    "administrative services manager",
    "adult education teacher",
    "advertising manager",
    "advertising sales agent",
    "aerobics instructor",
    "aerospace engineer",
    "aerospace engineering technician",
    "agent",
    "agricultural engineer",
    "agricultural equipment operator",
    "agricultural grader",
    "agricultural inspector",
    "agricultural manager",
    "agricultural sciences teacher",
    "agricultural sorter",
    "agricultural technician",
    "agricultural worker",
    "air conditioning installer",
    "air conditioning mechanic",
    "air traffic controller",
    "aircraft cargo handling supervisor",
    "aircraft mechanic",
    "aircraft service technician",
    "airline copilot",
    "airline pilot",
    "ambulance dispatcher",
    "ambulance driver",
    "amusement machine servicer",
    "anesthesiologist",
    "animal breeder",
    "animal control worker",
    "animal scientist",
    "animal trainer",
    "animator",
    "answering service operator",
    "anthropologist",
    "apparel patternmaker",
    "apparel worker",
    "arbitrator",
    "archeologist",
    "architect",
    "architectural drafter",
    "architectural manager",
    "archivist",
    "art director",
    "art teacher",
    "artist",
    "assembler",
    "astronomer",
    "athlete",
    "athletic trainer",
    "ATM machine repairer",
    "atmospheric scientist",
    "attendant",
    "audio and video equipment technician",
    "audio-visual and multimedia collections specialist",
    "audiologist",
    "auditor",
    "author",
    "auto damage insurance appraiser",
    "automotive and watercraft service attendant",
    "automotive glass installer",
    "automotive mechanic",
    "avionics technician",
    "baggage porter",
    "bailiff",
    "baker",
    "barback",
    "barber",
    "bartender",
    "basic education teacher",
    "behavioral disorder counselor",
    "bellhop",
    "bench carpenter",
    "bicycle repairer",
    "bill and account collector",
    "billing and posting clerk",
    "biochemist",
    "biological technician",
    "biomedical engineer",
    "biophysicist",
    "blaster",
    "blending machine operator",
    "blockmason",
    "boiler operator",
    "boilermaker",
    "bookkeeper",
    "boring machine tool tender",
    "brazer",
    "brickmason",
    "bridge and lock tender",
    "broadcast news analyst",
    "broadcast technician",
    "brokerage clerk",
    "budget analyst",
    "building inspector",
    "bus mechanic",
    "butcher",
    "buyer",
    "cabinetmaker",
    "cafeteria attendant",
    "cafeteria cook",
    "camera operator",
    "camera repairer",
    "cardiovascular technician",
    "cargo agent",
    "carpenter",
    "carpet installer",
    "cartographer",
    "cashier",
    "caster",
    "ceiling tile installer",
    "cellular equipment installer",
    "cement mason",
    "channeling machine operator",
    "chauffeur",
    "checker",
    "chef",
    "chemical engineer",
    "chemical plant operator",
    "chemist",
    "chemistry teacher",
    "chief executive",
    "child social worker",
    "childcare worker",
    "chiropractor",
    "choreographer",
    "civil drafter",
    "civil engineer",
    "civil engineering technician",
    "claims adjuster",
    "claims examiner",
    "claims investigator",
    "cleaner",
    "clinical laboratory technician",
    "clinical laboratory technologist",
    "clinical psychologist",
    "coating worker",
    "coatroom attendant",
    "coil finisher",
    "coil taper",
    "coil winder",
    "coin machine servicer",
    "commercial diver",
    "commercial pilot",
    "commodities sales agent",
    "communications equipment operator",
    "communications teacher",
    "community association manager",
    "community service manager",
    "compensation and benefits manager",
    "compliance officer",
    "composer",
    "computer hardware engineer",
    "computer network architect",
    "computer operator",
    "computer programmer",
    "computer science teacher",
    "computer support specialist",
    "computer systems administrator",
    "computer systems analyst",
    "concierge",
    "conciliator",
    "concrete finisher",
    "conservation science teacher",
    "conservation scientist",
    "conservation worker",
    "conservator",
    "construction inspector",
    "construction manager",
    "construction painter",
    "construction worker",
    "continuous mining machine operator",
    "convention planner",
    "conveyor operator",
    "cook",
    "cooling equipment operator",
    "copy marker",
    "correctional officer",
    "correctional treatment specialist",
    "correspondence clerk",
    "correspondent",
    "cosmetologist",
    "cost estimator",
    "costume attendant",
    "counseling psychologist",
    "counselor",
    "courier",
    "court reporter",
    "craft artist",
    "crane operator",
    "credit analyst",
    "credit checker",
    "credit counselor",
    "criminal investigator",
    "criminal justice teacher",
    "crossing guard",
    "curator",
    "custom sewer",
    "customer service representative",
    "cutter",
    "cutting machine operator",
    "dancer",
    "data entry keyer",
    "database administrator",
    "decorating worker",
    "delivery services driver",
    "demonstrator",
    "dental assistant",
    "dental hygienist",
    "dental laboratory technician",
    "dentist",
    "derrick operator",
    "designer",
    "desktop publisher",
    "detective",
    "diagnostic medical sonographer",
    "die maker",
    "diesel engine specialist",
    "dietetic technician",
    "dietitian",
    "dinkey operator",
    "director",
    "dishwasher",
    "dispatcher",
    "door-to-door sales worker",
    "drafter",
    "dragline operator",
    "drama teacher",
    "dredge operator",
    "dressing room attendant",
    "dressmaker",
    "drier operator",
    "drilling machine tool operator",
    "dry-cleaning worker",
    "drywall installer",
    "dyeing machine operator",
    "earth driller",
    "economics teacher",
    "economist",
    "editor",
    "education administrator",
    "electric motor repairer",
    "electrical electronics drafter",
    "electrical engineer",
    "electrical equipment assembler",
    "electrical installer",
    "electrical power-line installer",
    "electrician",
    "electro-mechanical technician",
    "elementary school teacher",
    "elevator installer",
    "elevator repairer",
    "embalmer",
    "emergency management director",
    "emergency medical technician",
    "engine assembler",
    "engineer",
    "engineering manager",
    "engineering teacher",
    "english language teacher",
    "engraver",
    "entertainment attendant",
    "environmental engineer",
    "environmental science teacher",
    "environmental scientist",
    "epidemiologist",
    "escort",
    "etcher",
    "event planner",
    "excavating operator",
    "executive administrative assistant",
    "executive secretary",
    "exhibit designer",
    "expediting clerk",
    "explosives worker",
    "extraction worker",
    "fabric mender",
    "fabric patternmaker",
    "fabricator",
    "faller",
    "family practitioner",
    "family social worker",
    "family therapist",
    "farm advisor",
    "farm equipment mechanic",
    "farm labor contractor",
    "farmer",
    "farmworker",
    "fashion designer",
    "fast food cook",
    "fence erector",
    "fiberglass fabricator",
    "fiberglass laminator",
    "file clerk",
    "filling machine operator",
    "film and video editor",
    "financial analyst",
    "financial examiner",
    "financial manager",
    "financial services sales agent",
    "fine artist",
    "fire alarm system installer",
    "fire dispatcher",
    "fire inspector",
    "fire investigator",
    "firefighter",
    "fish and game warden",
    "fish cutter",
    "fish trimmer",
    "fisher",
    "fitness studies teacher",
    "fitness trainer",
    "flight attendant",
    "floor finisher",
    "floor layer",
    "floor sander",
    "floral designer",
    "food batchmaker",
    "food cooking machine operator",
    "food preparation worker",
    "food science technician",
    "food scientist",
    "food server",
    "food service manager",
    "food technologist",
    "foreign language teacher",
    "foreign literature teacher",
    "forensic science technician",
    "forest fire inspector",
    "forest fire prevention specialist",
    "forest worker",
    "forester",
    "forestry teacher",
    "forging machine setter",
    "foundry coremaker",
    "freight agent",
    "freight mover",
    "fundraising manager",
    "funeral attendant",
    "funeral director",
    "funeral service manager",
    "furnace operator",
    "furnishings worker",
    "furniture finisher",
    "gaming booth cashier",
    "gaming cage worker",
    "gaming change person",
    "gaming dealer",
    "gaming investigator",
    "gaming manager",
    "gaming surveillance officer",
    "garment mender",
    "garment presser",
    "gas compressor",
    "gas plant operator",
    "gas pumping station operator",
    "general manager",
    "general practitioner",
    "geographer",
    "geography teacher",
    "geological engineer",
    "geological technician",
    "geoscientist",
    "glazier",
    "government program eligibility interviewer",
    "graduate teaching assistant",
    "graphic designer",
    "groundskeeper",
    "groundskeeping worker",
    "gynecologist",
    "hairdresser",
    "hairstylist",
    "hand grinding worker",
    "hand laborer",
    "hand packager",
    "hand packer",
    "hand polishing worker",
    "hand sewer",
    "hazardous materials removal worker",
    "head cook",
    "health and safety engineer",
    "health educator",
    "health information technician",
    "health services manager",
    "health specialties teacher",
    "healthcare social worker",
    "hearing officer",
    "heat treating equipment setter",
    "heating installer",
    "heating mechanic",
    "heavy truck driver",
    "highway maintenance worker",
    "historian",
    "history teacher",
    "hoist and winch operator",
    "home appliance repairer",
    "home economics teacher",
    "home entertainment installer",
    "home health aide",
    "home management advisor",
    "host",
    "hostess",
    "hostler",
    "hotel desk clerk",
    "housekeeping cleaner",
    "human resources assistant",
    "human resources manager",
    "human service assistant",
    "hunter",
    "hydrologist",
    "illustrator",
    "industrial designer",
    "industrial engineer",
    "industrial engineering technician",
    "industrial machinery mechanic",
    "industrial production manager",
    "industrial truck operator",
    "industrial-organizational psychologist",
    "information clerk",
    "information research scientist",
    "information security analyst",
    "information systems manager",
    "inspector",
    "instructional coordinator",
    "instructor",
    "insulation worker",
    "insurance claims clerk",
    "insurance sales agent",
    "insurance underwriter",
    "intercity bus driver",
    "interior designer",
    "internist",
    "interpreter",
    "interviewer",
    "investigator",
    "jailer",
    "janitor",
    "jeweler",
    "judge",
    "judicial law clerk",
    "kettle operator",
    "kiln operator",
    "kindergarten teacher",
    "laboratory animal caretaker",
    "landscape architect",
    "landscaping worker",
    "lathe setter",
    "laundry worker",
    "law enforcement teacher",
    "law teacher",
    "lawyer",
    "layout worker",
    "leather worker",
    "legal assistant",
    "legal secretary",
    "legislator",
    "librarian",
    "library assistant",
    "library science teacher",
    "library technician",
    "licensed practical nurse",
    "licensed vocational nurse",
    "life scientist",
    "lifeguard",
    "light truck driver",
    "line installer",
    "literacy teacher",
    "literature teacher",
    "loading machine operator",
    "loan clerk",
    "loan interviewer",
    "loan officer",
    "lobby attendant",
    "locker room attendant",
    "locksmith",
    "locomotive engineer",
    "locomotive firer",
    "lodging manager",
    "log grader",
    "logging equipment operator",
    "logistician",
    "machine feeder",
    "machinist",
    "magistrate judge",
    "magistrate",
    "maid",
    "mail clerk",
    "mail machine operator",
    "mail superintendent",
    "maintenance painter",
    "maintenance worker",
    "makeup artist",
    "management analyst",
    "manicurist",
    "manufactured building installer",
    "mapping technician",
    "marble setter",
    "marine engineer",
    "marine oiler",
    "market research analyst",
    "marketing manager",
    "marketing specialist",
    "marriage therapist",
    "massage therapist",
    "material mover",
    "materials engineer",
    "materials scientist",
    "mathematical science teacher",
    "mathematical technician",
    "mathematician",
    "maxillofacial surgeon",
    "measurer",
    "meat cutter",
    "meat packer",
    "meat trimmer",
    "mechanical door repairer",
    "mechanical drafter",
    "mechanical engineer",
    "mechanical engineering technician",
    "mediator",
    "medical appliance technician",
    "medical assistant",
    "medical equipment preparer",
    "medical equipment repairer",
    "medical laboratory technician",
    "medical laboratory technologist",
    "medical records technician",
    "medical scientist",
    "medical secretary",
    "medical services manager",
    "medical transcriptionist",
    "meeting planner",
    "mental health counselor",
    "mental health social worker",
    "merchandise displayer",
    "messenger",
    "metal caster",
    "metal patternmaker",
    "metal pickling operator",
    "metal pourer",
    "metal worker",
    "metal-refining furnace operator",
    "metal-refining furnace tender",
    "meter reader",
    "microbiologist",
    "middle school teacher",
    "milling machine setter",
    "millwright",
    "mine cutting machine operator",
    "mine shuttle car operator",
    "mining engineer",
    "mining safety engineer",
    "mining safety inspector",
    "mining service unit operator",
    "mixing machine setter",
    "mobile heavy equipment mechanic",
    "mobile home installer",
    "model maker",
    "model",
    "molder",
    "mortician",
    "motel desk clerk",
    "motion picture projectionist",
    "motorboat mechanic",
    "motorboat operator",
    "motorboat service technician",
    "motorcycle mechanic",
    "multimedia artist",
    "museum technician",
    "music director",
    "music teacher",
    "musical instrument repairer",
    "musician",
    "natural sciences manager",
    "naval architect",
    "network systems administrator",
    "new accounts clerk",
    "news vendor",
    "nonfarm animal caretaker",
    "nuclear engineer",
    "nuclear medicine technologist",
    "nuclear power reactor operator",
    "nuclear technician",
    "nursing aide",
    "nursing instructor",
    "nursing teacher",
    "nutritionist",
    "obstetrician",
    "occupational health and safety specialist",
    "occupational health and safety technician",
    "occupational therapist",
    "occupational therapy aide",
    "occupational therapy assistant",
    "offbearer",
    "office clerk",
    "office machine operator",
    "operating engineer",
    "operations manager",
    "operations research analyst",
    "ophthalmic laboratory technician",
    "optician",
    "optometrist",
    "oral surgeon",
    "order clerk",
    "order filler",
    "orderly",
    "ordnance handling expert",
    "orthodontist",
    "orthotist",
    "outdoor power equipment mechanic",
    "oven operator",
    "packaging machine operator",
    "painter ",
    "painting worker",
    "paper goods machine setter",
    "paperhanger",
    "paralegal",
    "paramedic",
    "parking enforcement worker",
    "parking lot attendant",
    "parts salesperson",
    "paving equipment operator",
    "payroll clerk",
    "pediatrician",
    "pedicurist",
    "personal care aide",
    "personal chef",
    "personal financial advisor",
    "pest control worker",
    "pesticide applicator",
    "pesticide handler",
    "pesticide sprayer",
    "petroleum engineer",
    "petroleum gauger",
    "petroleum pump system operator",
    "petroleum refinery operator",
    "petroleum technician",
    "pharmacist",
    "pharmacy aide",
    "pharmacy technician",
    "philosophy teacher",
    "photogrammetrist",
    "photographer",
    "photographic process worker",
    "photographic processing machine operator",
    "physical therapist aide",
    "physical therapist assistant",
    "physical therapist",
    "physician assistant",
    "physician",
    "physicist",
    "physics teacher",
    "pile-driver operator",
    "pipefitter",
    "pipelayer",
    "planing machine operator",
    "planning clerk",
    "plant operator",
    "plant scientist",
    "plasterer",
    "plastic patternmaker",
    "plastic worker",
    "plumber",
    "podiatrist",
    "police dispatcher",
    "police officer",
    "policy processing clerk",
    "political science teacher",
    "political scientist",
    "postal service clerk",
    "postal service mail carrier",
    "postal service mail processing machine operator",
    "postal service mail processor",
    "postal service mail sorter",
    "postmaster",
    "postsecondary teacher",
    "poultry cutter",
    "poultry trimmer",
    "power dispatcher",
    "power distributor",
    "power plant operator",
    "power tool repairer",
    "precious stone worker",
    "precision instrument repairer",
    "prepress technician",
    "preschool teacher",
    "priest",
    "print binding worker",
    "printing press operator",
    "private detective",
    "probation officer",
    "procurement clerk",
    "producer",
    "product promoter",
    "production clerk",
    "production occupation",
    "proofreader",
    "property manager",
    "prosthetist",
    "prosthodontist",
    "psychiatric aide",
    "psychiatric technician",
    "psychiatrist",
    "psychologist",
    "psychology teacher",
    "public relations manager",
    "public relations specialist",
    "pump operator",
    "purchasing agent",
    "purchasing manager",
    "radiation therapist",
    "radio announcer",
    "radio equipment installer",
    "radio operator",
    "radiologic technician",
    "radiologic technologist",
    "rail car repairer",
    "rail transportation worker",
    "rail yard engineer",
    "rail-track laying equipment operator",
    "railroad brake operator",
    "railroad conductor",
    "railroad police",
    "rancher",
    "real estate appraiser",
    "real estate broker",
    "real estate manager",
    "real estate sales agent",
    "receiving clerk",
    "receptionist",
    "record clerk",
    "recreation teacher",
    "recreation worker",
    "recreational therapist",
    "recreational vehicle service technician",
    "recyclable material collector",
    "referee",
    "refractory materials repairer",
    "refrigeration installer",
    "refrigeration mechanic",
    "refuse collector",
    "regional planner",
    "registered nurse",
    "rehabilitation counselor",
    "reinforcing iron worker",
    "reinforcing rebar worker",
    "religion teacher",
    "religious activities director",
    "religious worker",
    "rental clerk",
    "repair worker",
    "reporter",
    "residential advisor",
    "resort desk clerk",
    "respiratory therapist",
    "respiratory therapy technician",
    "retail buyer",
    "retail salesperson",
    "revenue agent",
    "rigger",
    "rock splitter",
    "rolling machine tender",
    "roof bolter",
    "roofer",
    "rotary drill operator",
    "roustabout",
    "safe repairer",
    "sailor",
    "sales engineer",
    "sales manager",
    "sales representative",
    "sampler",
    "sawing machine operator",
    "scaler",
    "school bus driver",
    "school psychologist",
    "school social worker",
    "scout leader",
    "sculptor",
    "secondary education teacher",
    "secondary school teacher",
    "secretary",
    "securities sales agent",
    "security guard",
    "security system installer",
    "segmental paver",
    "self-enrichment education teacher",
    "semiconductor processor",
    "septic tank servicer",
    "set designer",
    "sewer pipe cleaner",
    "sewing machine operator",
    "shampooer",
    "shaper",
    "sheet metal worker",
    "sheriff's patrol officer",
    "ship captain",
    "ship engineer",
    "ship loader",
    "shipmate",
    "shipping clerk",
    "shoe machine operator",
    "shoe worker",
    "short order cook",
    "signal operator",
    "signal repairer",
    "singer",
    "ski patrol",
    "skincare specialist",
    "slaughterer",
    "slicing machine tender",
    "slot supervisor",
    "social science research assistant",
    "social sciences teacher",
    "social scientist",
    "social service assistant",
    "social service manager",
    "social work teacher",
    "social worker",
    "sociologist",
    "sociology teacher",
    "software developer",
    "software engineer",
    "soil scientist",
    "solderer",
    "sorter",
    "sound engineering technician",
    "space scientist",
    "special education teacher",
    "speech-language pathologist",
    "sports book runner",
    "sports entertainer",
    "sports performer",
    "stationary engineer",
    "statistical assistant",
    "statistician",
    "steamfitter",
    "stock clerk",
    "stock mover",
    "stonemason",
    "street vendor",
    "streetcar operator",
    "structural iron worker",
    "structural metal fabricator",
    "structural metal fitter",
    "structural steel worker",
    "stucco mason",
    "substance abuse counselor",
    "substance abuse social worker",
    "subway operator",
    "surfacing equipment operator",
    "surgeon",
    "surgical technologist",
    "survey researcher",
    "surveying technician",
    "surveyor",
    "switch operator",
    "switchboard operator",
    "tailor",
    "tamping equipment operator",
    "tank car loader",
    "taper",
    "tax collector",
    "tax examiner",
    "tax preparer",
    "taxi driver",
    "teacher assistant",
    "teacher",
    "team assembler",
    "technical writer",
    "telecommunications equipment installer",
    "telemarketer",
    "telephone operator",
    "television announcer",
    "teller",
    "terrazzo finisher",
    "terrazzo worker",
    "tester",
    "textile bleaching operator",
    "textile cutting machine setter",
    "textile knitting machine setter",
    "textile presser",
    "textile worker",
    "therapist",
    "ticket agent",
    "ticket taker",
    "tile setter",
    "timekeeping clerk",
    "timing device assembler",
    "tire builder",
    "tire changer",
    "tire repairer",
    "title abstractor",
    "title examiner",
    "title searcher",
    "tobacco roasting machine operator",
    "tool filer",
    "tool grinder",
    "tool maker",
    "tool sharpener",
    "tour guide",
    "tower equipment installer",
    "tower operator",
    "track switch repairer",
    "tractor operator",
    "tractor-trailer truck driver",
    "traffic clerk",
    "traffic technician",
    "training and development manager",
    "training and development specialist",
    "transit police",
    "translator",
    "transportation equipment painter",
    "transportation inspector",
    "transportation security screener",
    "transportation worker",
    "trapper",
    "travel agent",
    "travel clerk",
    "travel guide",
    "tree pruner",
    "tree trimmer",
    "trimmer",
    "truck loader",
    "truck mechanic",
    "tuner",
    "turning machine tool operator",
    "typist",
    "umpire",
    "undertaker",
    "upholsterer",
    "urban planner",
    "usher",
    "valve installer",
    "vending machine servicer",
    "veterinarian",
    "veterinary assistant",
    "veterinary technician",
    "vocational counselor",
    "vocational education teacher",
    "waiter",
    "waitress",
    "watch repairer",
    "water treatment plant operator",
    "weaving machine setter",
    "web developer",
    "weigher",
    "welder",
    "wellhead pumper",
    "wholesale buyer",
    "wildlife biologist",
    "window trimmer",
    "wood patternmaker",
    "woodworker",
    "word processor",
    "writer",
    "yardmaster",
    "zoologist"
]
industries = [
    "Accounting",
    "Airlines/Aviation",
    "Alternative Dispute Resolution",
    "Alternative Medicine",
    "Animation",
    "Apparel & Fashion",
    "Architecture & Planning",
    "Arts & Crafts",
    "Automotive",
    "Aviation & Aerospace",
    "Banking",
    "Biotechnology",
    "Broadcast Media",
    "Building Materials",
    "Business Supplies & Equipment",
    "Capital Markets",
    "Chemicals",
    "Civic & Social Organization",
    "Civil Engineering",
    "Commercial Real Estate",
    "Computer & Network Security",
    "Computer Games",
    "Computer Hardware",
    "Computer Networking",
    "Computer Software",
    "Construction",
    "Consumer Electronics",
    "Consumer Goods",
    "Consumer Services",
    "Cosmetics",
    "Dairy",
    "Defense & Space",
    "Design",
    "Education Management",
    "E-learning",
    "Electrical & Electronic Manufacturing",
    "Entertainment",
    "Environmental Services",
    "Events Services",
    "Executive Office",
    "Facilities Services",
    "Farming",
    "Financial Services",
    "Fine Art",
    "Fishery",
    "Food & Beverages",
    "Food Production",
    "Fundraising",
    "Furniture",
    "Gambling & Casinos",
    "Glass, Ceramics & Concrete",
    "Government Administration",
    "Government Relations",
    "Graphic Design",
    "Health, Wellness & Fitness",
    "Higher Education",
    "Hospital & Health Care",
    "Hospitality",
    "Human Resources",
    "Import & Export",
    "Individual & Family Services",
    "Industrial Automation",
    "Information Services",
    "Information Technology & Services",
    "Insurance",
    "International Affairs",
    "International Trade & Development",
    "Internet",
    "Investment Banking/Venture",
    "Investment Management",
    "Judiciary",
    "Law Enforcement",
    "Law Practice",
    "Legal Services",
    "Legislative Office",
    "Leisure & Travel",
    "Libraries",
    "Logistics & Supply Chain",
    "Luxury Goods & Jewelry",
    "Machinery",
    "Management Consulting",
    "Maritime",
    "Marketing & Advertising",
    "Market Research",
    "Mechanical or Industrial Engineering",
    "Media Production",
    "Medical Device",
    "Medical Practice",
    "Mental Health Care",
    "Military",
    "Mining & Metals",
    "Motion Pictures & Film",
    "Museums & Institutions",
    "Music",
    "Nanotechnology",
    "Newspapers",
    "Nonprofit Organization Management",
    "Oil & Energy",
    "Online Publishing",
    "Outsourcing/Offshoring",
    "Package/Freight Delivery",
    "Packaging & Containers",
    "Paper & Forest Products",
    "Performing Arts",
    "Pharmaceuticals",
    "Philanthropy",
    "Photography",
    "Plastics",
    "Political Organization",
    "Primary/Secondary",
    "Printing",
    "Professional Training",
    "Program Development",
    "Public Policy",
    "Public Relations",
    "Public Safety",
    "Publishing",
    "Railroad Manufacture",
    "Ranching",
    "Real Estate",
    "Recreational",
    "Facilities & Services",
    "Religious Institutions",
    "Renewables & Environment",
    "Research",
    "Restaurants",
    "Retail",
    "Security & Investigations",
    "Semiconductors",
    "Shipbuilding",
    "Sporting Goods",
    "Sports",
    "Staffing & Recruiting",
    "Supermarkets",
    "Telecommunications",
    "Textiles",
    "Think Tanks",
    "Tobacco",
    "Translation & Localization",
    "Transportation/Trucking/Railroad",
    "Utilities",
    "Venture Capital",
    "Veterinary",
    "Warehousing",
    "Wholesale",
    "Wine & Spirits",
    "Wireless",
    "Writing & Editing"
]
