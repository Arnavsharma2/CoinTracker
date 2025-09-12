import csv
import os
class CoinTracker:
    def __init__(self): 
        self.base_url = 'https://api.coingecko.com/api/v3/'
        
        path = os.getcwd()
        self.exports_files = []
        for file in os.listdir(os.path.join(path, 'Portfolio Exports')):
            self.exports_files.append(os.path.join(path, 'Portfolio Exports', file))
    
        self.crypto_dict = self.parse_transactions(self.exports_files)
        print(self.crypto_dict)
    
    def parse_transactions(self, exports_files):
        crypto_dict = {}
        for read_file in exports_files:
            with open(read_file, 'r') as file:
                reader = csv.reader(file)
                
                for row in reader:
                    if row[0] != 'DATE':
                        
                        if row[5] != '' and row[5] not in crypto_dict:
                                crypto_dict[row[5]] = 0
                        if row[13] != '' and row[13] not in crypto_dict:
                                crypto_dict[row[13]] = 0
                                
                        if row[1] == 'withdrawal':
                            crypto_dict[row[5]] += float(row[4])
                        else:   
                            crypto_dict[row[13]] += float(row[12])
                                    
                            if row[4] != '':
                                crypto_dict[row[5]] += float(row[4])
                                
                            if row[6] != '':
                                crypto_dict[row[5]] += float(row[6])
        return crypto_dict
                    
                
if __name__ == "__main__":
    tracker = CoinTracker()
        
    
    
        
        
