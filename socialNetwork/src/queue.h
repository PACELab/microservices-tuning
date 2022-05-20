#include <iostream>
#include <sys/time.h>
#include <thread>
#include <unistd.h>
#include <fstream>

class proxyQueues{
    // Class: set a window of time to print the number of requests processed in that window. 
    // An infinite loop (spawned on a different thread) will wake up every window-size (assumed to be in milliseconds) period and output the number of requests processed in that window.
    // The incr method is called by the object when it starts processing a request. 
    // The thread (infinite loop in runQueueProbe) is part of the object and shares memory, so its easy to clear 

    private:
        int numReqs = 0;
        int objID = 0;

    public: 

        proxyQueues(int ipPrintWindowInMS,int objID): objID(objID) {
            std::cout<<" <proxyQueues>  objID "<<objID<<"\n";
        }

        void incrReqs(){
            numReqs+=1;
        }

        int getNReset_numReqs(){
            int temp_numReqs = numReqs;
            numReqs = 0;
            return temp_numReqs;
        }

        ~proxyQueues(){
            //reqOpFile.close();
            std::cout<<" <~proxyQueues> objID "<<objID<<"\n";
            std::cout<<" <proxyQueues> Alright, peace out!! \n";
        }
};

class queueContainer{

    private:
        double printWindowInMS = 0;
        int numObjs = 0;
        int startObjID = 0;
        int *numReqs;
        bool foundNonZero = false;

        double lastPrintedTS = 0;
        double curTS = 0.0;
        double prevTS = 0.0;
        struct timeval tempTimeVal;
        std::thread *thread_obj;

        int maxReqs = 1000*1000*1000; //might require a restart if and when the numSamples counter reaches this limit.
        int numSamples = 0;

        inline double getCurTS(){
            gettimeofday(&tempTimeVal,NULL);
            double curSampledTS = ((tempTimeVal.tv_sec*1000) + (double(tempTimeVal.tv_usec)/1000)); // time in ms
            return curSampledTS;
        }

        void runQueueProbe(){

            double diffTime = 0.0;

            lastPrintedTS = getCurTS();
            std::cout<<"\t <qC:rQP> header: sample-num\tcurTS\t numReqs\n";
            //reqOpFile.open(filename);
            std::cout<<"\t <qC:rQP> startObjID "<<startObjID<<" printWindowInMS: "<<printWindowInMS<<" diffTime "<<diffTime<<"\n";
            //reqOpFile<<"\t <pQ:rQP> objID "<<objID<<" printWindowInMS: "<<printWindowInMS<<" diffTime "<<diffTime<<"\n";

            int sleepTimeInUS = 1000*printWindowInMS-500;
            while(true){ // Infinite loop.

                curTS = getCurTS();
                diffTime = curTS-lastPrintedTS;
                foundNonZero = false;

                if(diffTime>printWindowInMS){

                    for(int i=0;i<numObjs;i++){
                        numReqs[i] = allQueueObjs[i]->getNReset_numReqs();
                        if(numReqs[i]!=0)
                            foundNonZero = true;
                    }
                    
                    // Since this is an infinite loop, printing when requests are zero will result in large log files.
                    // Will print only when there are requests. Should handle cases where samples are missing on the post-processing side.
                    if(foundNonZero){
                        for(int i=0;i<numObjs;i++){
                            std::cout<<"\t <qC:rQP> objID "<<(startObjID+i)<<"\t"<<numSamples<<"\t"<<std::to_string(curTS)<<"\t"<<numReqs[i]<<"\n"; 
                        }
                         std::cout<<"\n";
                    }

                    // WARNING: If a race condition happens, this could potentially reset few requests which were processed between printing the stats and clearing the counter. 
                    //          Not sure whether there is any performant solution to this.
                    lastPrintedTS = curTS;    
                    numSamples++;  
                    // Since I found a sample now, will sleep until 500us before the next window , that way, I won't waste CPU.
                    usleep(sleepTimeInUS);              
                }

                if(numSamples>maxReqs) break; // Using this kill switch while testing the uService.
            }
        }


    public:
        proxyQueues **allQueueObjs;// = new std::thread*[numObjs];

        queueContainer(int ipPrintWindowInMS,int startObjID,int numObjs): printWindowInMS(double(ipPrintWindowInMS)),numObjs(numObjs),startObjID(startObjID) {

            std::cout<<" <queueContainer>  start-objID "<<startObjID<<" numObjs "<<numObjs<<" printWindowInMS "<<printWindowInMS<<"\n";
            if(printWindowInMS<=0.5){
                std::cout<<"\t <proxyQueues> startObjID: "<<startObjID<<"\t printWindowInMS cannot be lower than 0.5 ms! \n";
                return;
            }

            allQueueObjs = new proxyQueues*[numObjs];
            numReqs = new int[numObjs];

            for(int i=0;i<numObjs;i++){
                allQueueObjs[i] = new proxyQueues(ipPrintWindowInMS,startObjID+i); 
            }

            thread_obj = new std::thread(&queueContainer::runQueueProbe,this);
            //runQueueProbe();            
        }

        ~queueContainer(){
            numSamples = maxReqs;
            if(thread_obj)
                thread_obj->join();            
            delete [] allQueueObjs;            
        }
};

