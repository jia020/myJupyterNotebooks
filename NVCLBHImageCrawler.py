from json import JSONDecodeError
import os
import requests
from io import BytesIO
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import pandas as pd


class NVCLBHImageCrawler:
    NVCL_DATASERVICE_URLS = {
        'VIC': 'https://geology.data.vic.gov.au/NVCLDataServices/',
        'NSW': 'https://gs.geoscience.nsw.gov.au/NVCLDataServices/',
        'WA': 'https://geossdi.dmp.wa.gov.au/NVCLDataServices/',
        'SA': 'https://sarigdata.pir.sa.gov.au/NVCLDataServices/',
        'NT': 'https://geology.data.nt.gov.au/NVCLDataServices/',
        'QLD': 'https://geology.information.qld.gov.au/NVCLDataServices/',
        'CSIRO': 'https://nvclwebservices.csiro.au/NVCLDataServices/',
        'TAS': 'https://www.mrt.tas.gov.au/NVCLDataServices/'
    }
    def __init__(self,pathToData):
        self.pathToData=pathToData
        self.csvFilePathBH = f'{pathToData}NVCL-Boreholes.csv'
        self.fo = open(f'{pathToData}/cellout.txt', 'a')

    def __del__(self):
        if self.fo:
            self.fo.close()
    def dual_print(self, *args, **kwargs):
        print(*args, **kwargs)
        print(*args, **kwargs, file=self.fo)

    def getLogInfo(self,prov:str,identifier:str)->dict:
        logID = ''
        sampleCount= 0 
        sectionID = ''
        #get logID
        url = f'{self.NVCL_DATASERVICE_URLS[prov]}getDatasetCollection.html'
        params = dict(
            holeidentifier=identifier,
            outputformat='json'
        )
        try:
            res = requests.get(url=url, params=params)
            resJson = res.json()
            imageLogCollection = resJson['datasetCollection'][0]['imageLogCollection']['imageLogCollection']
            for imageLog in imageLogCollection:
                if imageLog['logName'] == 'Imagery':
                    logID = imageLog['logID']
                    sampleCount = imageLog['sampleCount']
        except JSONDecodeError:
            self.dual_print(f'JSONDecodeError:{identifier=}')
        except Exception:                    
            self.dual_print(f'Exception:{identifier=}')

        #get sections
        sectionID = resJson['datasetCollection'][0]['sectionID']
        self.dual_print(f'{logID=}-{sampleCount=}-{sectionID=}')

        url = f'{self.NVCL_DATASERVICE_URLS[prov]}downloadscalars.html'
        params = dict(
            logid=sectionID,
            outputformat='json'
        )
        resJson={}
        res = requests.get(url=url, params=params)
        try:
            resJson = res.json()
        except JSONDecodeError:
            self.dual_print(f'JSONDecodeError:{sectionID=}')
        except Exception:
            self.dual_print(f'Exception:{sectionID=}')

        res:dict ={'logID':logID,'sampleCount':sampleCount,'sections':resJson}
        return res
    
    def download(self, prov:str, identifier:str, bhInfo:any,num:int=999999, simulation:bool = False)->int:
        sections = bhInfo['sections']
        url = f'{self.NVCL_DATASERVICE_URLS[prov]}Display_Tray_Thumb.html?logid={bhInfo['logID']}&sampleno='

        step = len(sections)//num  + 1
        count = 0
        print('DownloadingStart:Section',end='')
        for cc, section in enumerate(sections):
            if cc%step!=0:
                continue
            print(f'-{cc}',end='')
            if 'STARTDEPTH' in section:
                startDepth = int(section['STARTDEPTH'])
                endDepth = int(section['ENDDEPTH'])
                scal1 = int(section['SCAL1'])            
            else:
                startDepth = int(section['StartDepth'])
                endDepth = int(section['EndDepth'])
                scal1 = int(section['Scal1'])
            fileName = f'{prov}-{identifier}-SEC{scal1}-S{startDepth}-E{endDepth}.jpg'
            if not simulation:
                section_list = []
                for sampleCount in range(startDepth,endDepth+1):
                    try:
                        with requests.get(f'{url}{sampleCount}') as r:
                            section_list.append(plt.imread(BytesIO(r.content),'JPEG'))
                    except Exception as ex:
                        print(f'download: Exception:{str(ex)}')
                        break
                section_arr = np.concatenate(section_list)
                section_im = Image.fromarray(section_arr)
                section_im.save(os.path.join(self.pathToData, fileName), "JPEG")
            count += 1

        print('-End')
        return count
    
    def crawImageForOneBH(self, state:str, nvcl_id:str, num:int=999999, simulation:bool = False) -> int:
        count = 0
        try:
            bhInfo = self.getLogInfo(state,nvcl_id)
            if 'logID' in bhInfo:
                count = self.download(state,nvcl_id,bhInfo,num,simulation)
            else:
                print(f'crawImageForOneBH:error:{bhInfo=}')
        except Exception as ex:
            print(str(ex))
        return count
                    
    def crawlImage(self,indexStart:int = 0,num:int=999999,simulation:bool = False):
        self.dual_print(f'crawlImage:Start:{indexStart=}')
        df = pd.read_csv(self.csvFilePathBH).dropna(subset=["State","BoreholeURI"])
        cc=0
        for row in df.itertuples():
            myState = row.State.upper()
            if (row.Index < indexStart):
                continue 
            nvcl_id = row.BoreholeURI.rsplit('/', 1)[-1]
            self.dual_print(f'->index:Start:{row.Index}:{cc=}:{myState=}:{nvcl_id=}')
            count = self.crawImageForOneBH(myState, nvcl_id,num,simulation)
            self.dual_print(f'index:End:{row.Index}:{count=}')
            cc += 1
        self.dual_print('crawlImage:End')

def main():
    imageCrawer:NVCLBHImageCrawler = NVCLBHImageCrawler(r'C:/Backup/github/jia020/myJupyterNotebooks/Data/')
    #imageCrawer.crawImageForOneBH('NSW','PET_000389',num=3,simulation=False)
    imageCrawer.crawImageForOneBH('SA','227935',num=3,simulation=False)
    #imageCrawer.crawlImage(indexStart=99,num=10)#,simulation=True)
    #imageCrawer.crawlImage(simulation=True)                     
if __name__ == "__main__":
    main()
       