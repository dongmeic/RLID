# Match RLID address points with [MSAG (Master Street Address Guide)](https://nenawiki.org/wiki/MSAG_(Master_Street_Address_Guide))

The task is to compare the MSAG range between the RLID address points and the Intrado extract. The data folder is G:\projects\Address_Points\9-1-1_Net. 

## Steps

1. Read (and clean) data on address points, MSAG range, and the Intrado extract table;

The clean step is to make sure the emergency service number (ESN), street name (STREET), road type (STCODE), house number range in low (LOW) and high (HIGH), city name (CITY) and city code (CTCODE) are in the same format between datasets, to create an unique key for the match. 

2. Compare the MSAG range and Intrado extract table by different cases;

(1) Exactly matched - ESN, DI, STREET, STCODE, CTCODE, LOW, and HIGH are all the same between the two datasets, code 1;

(2) No match on the high house number range, code 2;

(3) No match on the low house number range, code 3;

(4) Missing ESN in the Intrado extract, code 4;

(5) No match on the house number range, code 5;

(6) No match on the ESN and possibly mismatched on the house number range, code 6;

(7) No match on the road type and possibly mismatched on the house number range and ESN, code 7;

(8) No match, code 0

3. Compare the address points and Intrado extract table by different cases;

(1) Exactly matched - ESN, DI, STREET, STCODE, and CTCODE are matched and the house number in the address points are within the house number range in the Intrado extract table, code 1;

(2) Outside of the house number range in the Intrado extract table in the high value, code 2;

(3) Outside of the house number range in the Intrado extract table in the low value, code 3;

(4) Outside of the house number range in the Intrado extract table when there is more than one range, code 4;

(5) Missing ESN in the Intrado extract, code 5;

(6) No match, code 0

4. Write up the match notes on the MSAG range and address points, and export data.
