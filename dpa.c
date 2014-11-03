/*
  ECM Driver. 
  To compile: gcc -pthread -o ecm ecm.c
  To run: ./ecm&
  Make sure to load capes first.
  Be sure to use 0xAC for the MID of the BBOne when writing software
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>
#include <time.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <errno.h>
#include <pthread.h>
#include <netinet/in.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include "bb_gpio.h"

#define NANO 1000000000L
#define BIT_TIME 104170
#define TENTH_BIT_TIME 10417
#define TWELVEBITTIMES BIT_TIME * 12


struct timespec diff(struct timespec start, struct timespec end);
//int open_gpio(char* gp_path);
int read_gpio();
int read_j1708_message(int serial_port , char* buf, pthread_mutex_t *lock);
int difftimenanos(struct timespec diffspec);
int synchronize();
void ppj1708(int len, char* msgbuf);
char j1708_checksum(int len, char* msgbuf);
void wait_for_quiet(int gpio_fd,int priority, pthread_mutex_t *lock);
static void iosetup(void);

int mem_fd;
char *gpio_mem, *gpio_map;
volatile unsigned *gpio;

struct sockaddr_in my_addr;
struct sockaddr_in other_addr;
int read_socket;
pthread_mutex_t buslock;
int fd;
struct termios options;

void * ReadThread(void* args){
  int len;
  int check;
  int gpio;
  char msg_buf[256];
  //  gpio = open_gpio("/sys/class/gpio/gpio60/value");

  synchronize();
  tcflush(fd,TCIFLUSH);
  while(1){
    len = read_j1708_message(fd,msg_buf, &buslock);
    check = j1708_checksum(len,msg_buf);
    if(!check && len != 0){
      //      printf("%s\n","Sending to ECM:");
      //      ppj1708(len,msg_buf);
      sendto(read_socket,msg_buf,len,MSG_DONTWAIT,(struct sockaddr *) &other_addr, sizeof(other_addr));
    }
   }

}

void * WriteThread(void* args){
  int gpio;
  int len;
  int len2;
  char msg_buf[256];
  int client_size = sizeof(other_addr);

  struct timespec sleepspec;
  sleepspec.tv_sec = 0;
  sleepspec.tv_nsec = BIT_TIME*2;

  struct timespec clearspec;
  clearspec.tv_sec = 0;
  clearspec.tv_nsec = 0;

  //  gpio = open_gpio("/sys/class/gpio/gpio60/value");

  while(1){
    len = recvfrom(read_socket,msg_buf,256,0,(struct sockaddr *) &other_addr, &client_size);
    if(msg_buf[1] == 0xFE){
      //      printf("%s\n","Sending to DPA");
      //      ppj1708(len,msg_buf);
    }
    clearspec.tv_nsec = TENTH_BIT_TIME*14*len;
    wait_for_quiet(gpio,6,&buslock);
    


    //fprintf(stderr,"sending a message!\n");
    write(fd,msg_buf,len);

    nanosleep(&clearspec,NULL);
    len2 = read(fd,&msg_buf,len);
    
    pthread_mutex_unlock(&buslock);
    nanosleep(&sleepspec,NULL);
  }

}

int main(int argc, char* argv[]){
  //char* sock_name = "/tmp/ECM";
  //char* client_name = "/tmp/DPA";
  void* status;
  pthread_t threads[2];
  int rcw;
  int rcr;
  int i;

  iosetup();
  fd = open("/dev/ttyO4",O_RDWR|O_NOCTTY|O_NONBLOCK);

  tcgetattr(fd, &options);

  cfsetispeed(&options,B9600);
  cfsetospeed(&options,B9600);


  cfmakeraw(&options);

  tcsetattr(fd,TCSANOW,&options);
  

  /*Get the socket set up*/
  //unlink(sock_name);

  
  memset(&my_addr,0,sizeof(my_addr));
  my_addr.sin_family = AF_INET;
  my_addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
  my_addr.sin_port = htons(6971);

  memset(&other_addr,0,sizeof(other_addr));
  other_addr.sin_family = AF_INET;
  other_addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
  other_addr.sin_port = htons(6972);


  read_socket = socket(PF_INET, SOCK_DGRAM, 0);
  if(read_socket < 0){
    printf("%s\n","Could not open socket.");
  }
  if(bind(read_socket, (struct sockaddr *) &my_addr, sizeof(my_addr)) < 0)
    printf("%s\n","Could not bind DPA socket.");

  pthread_mutex_init(&buslock,NULL);

  rcr = pthread_create(&threads[0], NULL, ReadThread, NULL);
  rcw = pthread_create(&threads[1], NULL, WriteThread, NULL);

  for(i=0;i<2;i++){
    pthread_join(threads[i],&status);
  }

  pthread_exit(NULL);
 
}

char j1708_checksum(int len, char* msgbuf){
  char total = 0;
  int i;
  for(i=0;i<len-1;i++){
    total += msgbuf[i];
    total &= 0xFF;
  }

  return total + msgbuf[len-1];
}

void ppj1708(int len, char* msgbuf){
  int i;
  for(i = 0; i<len; i++){
    printf("%hhX,",msgbuf[i]);

  }
  printf(" Checksum: %hhX\n",j1708_checksum(len,msgbuf));
  

}

struct timespec diff(struct timespec start, struct timespec end)
{
  struct timespec temp;
  if ((end.tv_nsec-start.tv_nsec)<0) {
    temp.tv_sec = end.tv_sec-start.tv_sec-1;
    temp.tv_nsec = NANO+end.tv_nsec-start.tv_nsec;
  } else {
    temp.tv_sec = end.tv_sec-start.tv_sec;
    temp.tv_nsec = end.tv_nsec-start.tv_nsec;
  }
  return temp;
}

int difftimenanos(struct timespec diffspec){
  return diffspec.tv_sec * NANO + diffspec.tv_nsec;
}

/*int open_gpio(char* gp_path){
  return open(gp_path, O_RDONLY | O_NONBLOCK);
  }*/

int read_gpio(){
  return *(gpio + GPIO_IN) & GPIO0_7;
  }



int synchronize(){
  struct timespec start;
  struct timespec temp_time;
  int synced = 0;

  clock_gettime(CLOCK_REALTIME, &start);
  while(!synced){
    clock_gettime(CLOCK_REALTIME, &temp_time);
    if(read_gpio()){
      //      printf("%d\n",difftimenanos(diff(start,temp_time)));
      if(difftimenanos(diff(start,temp_time)) >= TWELVEBITTIMES)
	synced = 1;
    }else{
      start.tv_sec = temp_time.tv_sec;
      start.tv_nsec = temp_time.tv_nsec;
    }
  }
}


int read_j1708_message(int serial_port, char* buf, pthread_mutex_t *lock){
  int chars = 0;
  int status = 0;
  int retval = 0;


  //inter-char timeout
  struct timespec timeout;
  timeout.tv_sec = 0;
  //CHANGE THIS FOR DETROIT DIESEL/CAT
  timeout.tv_nsec = TENTH_BIT_TIME * 100;
  
  fd_set fds;
  FD_ZERO (&fds);
  FD_SET (serial_port,&fds);
 
  status = pselect(serial_port + 1, &fds, NULL, NULL, NULL, NULL);//timeout=NULL => block indefinitely
  pthread_mutex_lock(lock);

  while(pselect(serial_port + 1, &fds, NULL, NULL, &timeout, NULL)){
    retval = read(serial_port,&buf[chars],1);
    ++chars;
  }

  pthread_mutex_unlock(lock);
  return chars;

}

void wait_for_quiet(int gpio_fd,int priority,pthread_mutex_t *lock){
  int res;
  struct timespec start;
  struct timespec temp_time;
  long int duration = 10*BIT_TIME + 2*BIT_TIME * priority;
  int quiet = 0;

  pthread_mutex_lock(lock);
  clock_gettime(CLOCK_REALTIME,&start);
  while(!quiet){
    clock_gettime(CLOCK_REALTIME, &temp_time);
    if(read_gpio()){
      if(difftimenanos(diff(start,temp_time)) >= duration)
	quiet = 1;
      
    }else{

      pthread_mutex_unlock(lock);
      pthread_mutex_lock(lock);

      start.tv_sec = temp_time.tv_sec;
      start.tv_nsec = temp_time.tv_nsec;
    }

  }

  
}

static void iosetup(void){

  /* open /dev/mem */
  if ((mem_fd = open("/dev/mem", O_RDWR|O_SYNC) ) < 0) {
    printf("can't open /dev/mem \n");
    exit (-1);
  }

  /* mmap GPIO */
  gpio_map = (char *)mmap(
			  0,
			  GPIO_SIZE,
			  PROT_READ|PROT_WRITE,
			  MAP_SHARED,
			  mem_fd,
            GPIO0_BASE
			  );

  if (gpio_map == MAP_FAILED) {
    printf("mmap error %d\n", (int)gpio_map);
    exit(-1);
  }

  // Always use the volatile pointer!
  gpio = (volatile unsigned *)gpio_map;



}

/*void wait_for_quiet(int gpio_fd,int priority,pthread_mutex_t *lock){
  fd_set exceptfds;
  int res;
  int len;
  char* dummy[64];
  struct timespec timeout;
  struct timespec sleepspec;

  pthread_mutex_lock(lock);

  timeout.tv_sec = 0;
  timeout.tv_nsec = 10*BIT_TIME + 2 * BIT_TIME * priority;

  sleepspec.tv_sec = 0;
  sleepspec.tv_nsec = BIT_TIME*4;
  

  FD_ZERO(&exceptfds);
  FD_SET(gpio_fd,&exceptfds);


   This might require some explanation. The GPIO pin is set to trigger an event
     on a rising or falling edge. The default state of a J1708 bus is HIGH, and the standard
     requires that sending clients wait to see *n* consecutive high bits (idle bus)
     before sending. If the pselect call returns before it times out, it's seen an edge and
     therefore the bus is not quiet. If it times out, the bus is quiet.

     This is *kind of* busy waiting, which is bad, but using pselect should hopefully reduce
     the impact.
  
  lseek(gpio_fd,0,SEEK_SET);
  len = read(gpio_fd,dummy,1);

  while(res=pselect(gpio_fd+1,NULL,NULL,&exceptfds,&timeout,NULL)){
    lseek(gpio_fd,0,SEEK_SET);
    len = read(gpio_fd,dummy,1);
    pthread_mutex_unlock(lock);
    pthread_mutex_lock(lock);
  }
}*/

