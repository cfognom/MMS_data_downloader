# MMS data downloader

MMS_data_downloader can manage you local MMS database by:
  - Downloading files from 'requests' while skipping files already found locally
  - Removing outdated files
  - Re-downloading damaged* files
    
    *A file is regarded as 'damaged' if it's up-to-date but there is a size mismatch between it and the file on the server

## Usage
1. Clone or download the repository.

2. Open config.yaml and provide the following:
  
    1. dataRootPath: The path to the root location of your local MMS database.
    
    2. n_concurrentConnections: How many concurrent connections to use.  
       More means faster download rate but more CPU and RAM stress.  
       One connection equals about 0.4 Mbps.
         
    3. Under 'requests' specify your requests using the syntax shown below.  
       Information about the request parameters can be found here: https://lasp.colorado.edu/mms/sdc/public/about/how-to/  
       It can handle several requests at once by writing them below eachother.

Request syntax:  
  Replace values in parenthesis.
```
  (name of request):
    file: (file)
    sc_id: (sc_id)
    instrument_id: (instrument_id)
    data_rate_mode: (data_rate_mode)
    data_level: (data_level)
    descriptor: (descriptor)
    version: (version)
    start_date: (start_date)
    end_date: (end_date)
```
Example request:
```
  fgm201601:
    file:
    sc_id: mms1
    instrument_id: fgm
    data_rate_mode: srvy
    data_level: l2
    descriptor:
    version:
    start_date: 2016-01-01
    end_date: 2016-02-01
```

         
3. Run 'MMS_data_downloader.exe'.
  
    1. A summary of what needs to be downloaded will be shown.
      
    2. If any outdated files were found you will be promted to delete them.
      
    3. The download begins when you accept it.

## Authors

* **Carl Foghammar Nömtak** - [cfognom](https://github.com/cfognom)

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details
