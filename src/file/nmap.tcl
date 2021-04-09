#!/usr/bin/env tclsh

# Debugged by d3d using TCLPro Debugger


set timeout 1
set timeoutms 500
set waittime 4000
set svcarraymax 4096
set reasoncode 0
set reason "NULL"

proc syntaxhelp {} {
  puts stdout  "\7================================================================"
  puts stdout  "IOScan 0.1"
  puts stdout  "  Usage: IOScan <Scan Type> <Options> <target specifications>"
  puts stdout  "HOST DISCOVERY:"
  puts stdout  "  -P0/PN  Treat all hosts as online - skip Ping test"
  puts stdout  "  -SL  List hosts and ports to scan"
  puts stdout  "SCAN TYPE:"
  puts stdout  "  -sP  Ping scan only <ICMP ECHO>"
  puts stdout  "  -sT  TCP Connect Scan"
  puts stdout  "  -sU  UDP Scan"
  puts stdout  "  --reason:  display the reason a port state is reported as such"
  puts stdout  "PORT SPECIFICATION:"
  puts stdout  "  -p <port ranges> Specify ports to scan.  "
  puts stdout  "     -p22  Scan port 22"
  puts stdout  "     -p22,23,135-139,445  Scan ports 22, 23, 135, 136, 137, 138, 139, 445"
  puts stdout  "TARGET SPECIFICATION:"
  puts stdout  "  CIDR, IP range and single IPs are all a supported - comma delimited"
  puts stdout  "  For example:"
  puts stdout  "    192.168.10.0/24,192.168.17.21-34,192.168.40.1"
}

proc memcalc { scantype } {
 global iplist
 global portlist
 if { $scantype == "T" } {
     set gradient 1544
     set intercept 2568474
 } else {
     set gradient 30279
     set intercept 3120161
 }
 set factor1 50   ; # watermark to ask for a y/n to proceed
 set factor2 75   ; # watermark to force an exit
 set ipcount [ llength $iplist ]
 set portcount [ llength $portlist ]
 set calcmem [ expr ($portcount * $ipcount * $gradient ) ]
 set calcmem [ expr ( $calcmem + $intercept) ]
 set i [ exec "sho proc mem | i Processor Pool" ]
 set memfree [ lindex $i [ expr ( [llength $i] - 1 ) ]]
 set memlimit1 [ expr ($memfree / 100 * $factor1 ) ]
 set memlimit2 [ expr ($memfree / 100 * $factor2 ) ]
 puts stdout "Free Memory on Platform = $memfree  / Memory required for this scan = $calcmem"
 puts stdout " "
 if { $calcmem > $memlimit2 } {
     puts stdout "\7The resources estimated for your scan will exceed $factor2\%"
     puts stdout  "of your available memory total of $calcmem"
     puts stdout "Execution cannot proceed without impacting primary device functions"
     return 1
 } elseif { $calcmem < 0 } {
     puts stdout "\7The resources used by your scan will exceed the physical memory installed"
     puts stdout "on your platform.  Execution cannot proceed without impacting"
     puts stdout "primary device functions"
     return 1
 } elseif { $calcmem > $memlimit1 } {
     puts stdout "\7The resources used by your scan will exceed $factor1%"
     puts stdout "of your available memory total of $calcmem"
     puts stdout "This may impact primary device functions"
     puts -nonewline stdout "do you wish to proceed (y/n) ==> "
     flush stdout
     set response [ gets stdin ];
     if { $response == "y" } { return 0 } else { return 1 }
  } elseif { $calcmem < $memlimit1 } { return 0 }
}


proc IPtoHex { IP } {
     binary scan [binary format c4 [split $IP .]] H8 Hex
     return $Hex
}

proc hex2dec {hexvalue} {
  set decvalue [format "%u" [expr 0x$hexvalue]]
  return $decvalue
}

proc dec2hex { decvalue } {
  set hexvalue [format "%#010X" [expr $decvalue]]
  return $hexvalue
}

 proc Hex2IP { Hex } {
     # first trim off leading "0x" if it's there
     if {  [string length $Hex] == 10 } { set Hex [string range $Hex 2 9] }

     binary scan [binary format H8 $Hex] c4 IPtmp
     foreach num $IPtmp {
 	lappend IP [expr ($num + 0x100) % 0x100]
     }
     set IP [join $IP .]
     return $IP
}


 proc isipvalid { IP } {
     # only digits'n'dots
     regsub -all {[.0-9]} $IP {} scratchvar
     if { $scratchvar != "" } {
         return 0
     }

     # 4 octets means exactly 3 dots
     regsub -all {[0-9]} $IP {} scratchvar
     if { $scratchvar != "..." } {
         return 0
     }

     # is each octet betw 0 and 255?
     foreach b [split $IP .] {
     if { [string length $b] == 0 } {
         return 0
         }
         set ob $b
          #parse out leading zeros
         scan $b %d b
         if { $b < 0 | $b > 255 } {
             return 0
         }
     }
     return 1
 }

 proc iscidrvalid { CIDR } {
     # numeric check
     regsub -all {[0-9]} $CIDR {} scratchvar
     if { [string length $scratchvar] != 0 } {
     return 0
     }

     #convert to numeric, check values
     #because this is running on a router, mask <8 is not acceptable due to scan time.
     # mask of /31 or /32 is also not acceptable
     scan $CIDR %d CIDR
    if { $CIDR < 8 | $CIDR > 30 } {
      return 0
     }
     return 1
 }


proc ipCIDR { net } {
   global iplist

   set work1 [ split $net / ]
   set ip1 [ lindex $work1 0 ]

   if { ! [isipvalid $ip1 ] }   {
      puts stdout "\7Invalid IP address specified ==> $ip1"
      puts " "
      return 1
    }

    scan $net {%d.%d.%d.%d/%d} a b c d bits

    if { ! [iscidrvalid $bits ] }   {
      puts stdout "Invalid Netmask address specified ==> /$bits"
      puts stdout "Because of platform considerations, subnet mask must be >=8 or <=30"
      puts " "
      return 1
    }

    set hexmask [expr {0xffffffff & (0xffffffff << (32-$bits))}]
    set bnet [ hex2dec [IPtoHex $ip1] ]
    set realnet [ expr $bnet & $hexmask ]
    set firstip [expr $realnet+1 ]
    set bcast [expr $bnet | ( $hexmask ^ 0xffffffff )]
    set lastip [expr $bcast - 1]

    for { set j $firstip } { $j <= $lastip } { incr j} {
        set work1 [dec2hex $j]
        lappend iplist [ Hex2IP $work1 ]
    }
    return 0
}


proc iprange { net } {
   global iplist
   set work1 [ split $net - ]
   set ip1 [ lindex $work1 0 ]
   set maxoct4 [lindex $work1 1]

   if { ! [isipvalid $ip1 ] }   {
      puts stdout "Invalid IP address specified ==> $ip1"
      return 1
   }
   scan $ip1 {%d.%d.%d.%d} a b c d

   set ipmax $a.$b.$c.$maxoct4

   if { ! [isipvalid $ipmax] } {
      puts stdout "Invalid IP address specified ==> $ipmax"
      return 1
   }

   if { $d > $maxoct4 }  {
      puts stdout "Invalid IP address range specified ==> $ip1-$maxoct4"
      return 1
   }
   for { set j $d} {$j <= $maxoct4 } { incr j} {
      lappend iplist $a.$b.$c.$j
   }
   return 0
}


proc parsenet { networklist } {
    global iplist
    set netlist [split $networklist ,]

    foreach net $netlist  {
       if { [string first / $net] >0 } {
           set retval [ipCIDR $net]
    } elseif { [ string first - $net] >0} {
           set retval [iprange $net]
    }  else {
           if { ! [isipvalid $net] } {
               puts stdout "Invalid IP address specified ==> $net"
               return 1
           }
           lappend iplist $net }
    }
    return 0
}


proc pinger {ip timeout} {
    set pingretry 3
    # returns a 1 if any icmp echo replies make it back, otherwise returns a 0
    if { [regexp "(!)" [exec "ping $ip timeout $timeout repeat $pingretry" ]] } { return 1 } else { return 0 }
}

proc scantcpconnect {host port} {
    global timeout
    global reason

    set timeout1 [expr $timeout*1000 ]
    catch { socket $host $port } sock
    after $timeout1
    if { [string first sock $sock] == 0} {
        catch { close $sock }
        set reason "syn-ack"
        return "open  "
    } else { set reason "connection failed" ; return "closed" }
}

proc udpscan { ip port } {
    # timers should be global, logfile should NOT be global
    global timeoutms
    global waittime
    global reason

    ios_config "no logging buffer"
    ios_config "logging buff 8192 debug"

    set retcode "error"   ; # just in case, give retcode a value

    # set up the list of interesting packets to look for (ie set up packet capture filter)

    ios_config "access-list 111 permit udp any host $ip eq $port"
    ios_config "access-list 111 permit udp host $ip eq $port any"
    ios_config "access-list 111 permit icmp host $ip any unreach"

    # now, watch for these packets (ie start your packet capture)
    exec "debug ip packet 111 det"

    # next, send test udp packets to trigger responses
    ios_config "ip sla monitor 111" "type udpEcho dest-ipaddr $ip dest-port $port control disable" "time $timeoutms" "freq 1"
    ios_config "ip sla mon schedule 111 life forever start now"

    after $waittime             ; # wait - 2sec is generally enough for the log to catch up

    # now clean up confg and debug changes
    exec "no debug ip pack 111 det"
    ios_config "no access-list 111"
    ios_config "no ip sla monitor 111"

    set startpos "dst=$port"
    set logfile [ exec "show log" ]

    set ipstart 0
    set portunreach 0
    set unreach 0

    # first, find the last occurance of our target in the log

    set ipstart [ string first $startpos $logfile ]

    #now, look for icmp type 3, or icmp type 3 code 3, occuring after this ip value
    # (ie - make sure we're not reading a previous status).
    if { $ipstart > 0 } {
         set unreach [ string last "ICMP type=3" $logfile  ]
         set portunreach [ string last "ICMP type=3, code=3" $logfile  ]
         set udpreturn [ string last "UDP src=$port" $logfile ]
         set retcode "open/filtered"         ; # set the case for no packets back at all
         set reason "No Response"
         if { $unreach > $ipstart } { set retcode "filtered" ; set reason "ICMP Unreachable" }
         if { $portunreach > $ipstart } { set retcode "closed" ; set reason "ICMP Port Unreachable"}
         if { $udpreturn > $ipstart } { set retcode "open" ; set reason "UDP response" }
    } else { set retcode "open/filtered" ; set reason "No Response" }   ;  # this accounts for no packets back on empty logfile
    return $retcode
}


proc scanit {localportlist localnetworklist scantype pingit} {
global timeout
global reason
global reasoncode

foreach host $localnetworklist {

   # set existance default in case -P0 (no ping) is specified
   set hostexist 1
   if {$pingit == 1} { set hostexist [pinger $host $timeout] }

   if { $scantype == "P" } {
      if { $hostexist ==1 } {
          puts stdout "Host $host is up"
          } else { puts stdout "Host $host is down" }
      } else {

          if {$hostexist == 1 } {
             puts stdout "Interesting ports on host $host"
             puts -nonewline stdout "PORT     STATE"
             if {$reasoncode == 1} {puts -nonewline stdout "    REASON"}
              puts ""

             foreach port $localportlist {
                if { $scantype == "T" } {
                    set state [ scantcpconnect $host $port ]
                    set proto "tcp"
                } elseif {$scantype == "U" } {
                    set state [udpscan $host $port ]
                    set proto "udp"
                } elseif {$scantype == "L" } {
                    set proto "tcp"
                    set state "unscanned"
                }

             puts -nonewline stdout "$port/$proto   $state"
             if {$reasoncode == 1} { puts -nonewline stdout "    $reason"}
             puts stdout ""
          }
        } else { puts stdout "Host $host is unavailable" }
            puts stdout "\n\n"
        }
     }
return
}

proc parseports { ports } {

   global portlist
   set localportlist [split $ports ,]

   foreach port $localportlist {
      if {[string first - $port] > 0} {
         set localplist [split $port -]
         for {set lport [lindex $localplist 0]} {$lport <= [lindex $localplist 1]} {incr lport} {
              if {$lport > 0 && $lport <65535 } {
                  lappend portlist $lport
              } else {
                  puts stdout "Invalid port value ==> $lport"
                  return 1
              }
         }

      } else {
              if {$port >0 && $port <65535 } {
                  lappend portlist $port
              } else {
                  puts stdout "Invalid port value ==> $port"
                  return 1
              }
      }
   }
return 0
}

proc run { args } {
    global portlist
    global iplist
    global pingit
    global scantype

    catch {unset pingit}
    set pingit 1          ; # ping scan set to no (should be yes)
    catch {unset scantype}
    set scantype T        ; # default scan is TCP
    catch {unset iplist}
    set iplist {}
    catch unset portlist
    set portlist {}

    #process cmd line arguments
    foreach arg $args  {
          switch -glob -- $arg {
              -sU   {set scantype U}
              -sT   {set scantype T}
              -sP   {set scantype P ; set ports 1}
              -sL   {set scantype L ; set ports 1 ; set pingit 0}
              -P0   {set pingit 0}
              -PN   {set pingit 0}
              -p*   {set ports $arg}
              --reason { set reasoncode 1 }
              -h     {  set scantype "H" }
              default {set network $arg}
              }
           }

        # dump out intro line
        puts stdout "\n\n"
        puts stdout [clock format [clock seconds] -format {Starting IOSmap 0.9 ( http://www.defaultroute.ca ) at %Y-%m-%d %H:%M %Z}]
        puts ""


    if {$scantype != "H" } {

        # trim "-p out of ports arg, parse out the ports to a list of discrete values
        set ports [string trimleft $ports -p]
        set ok1 [parseports  $ports]

        # parse network values out to a discrete list of ip addresses
        set ok2 [parsenet $network]

        set ok [expr $ok1+$ok2 ]

        if { $ok == 0 } {

            set retcode [ memcalc $scantype ]

            if {$retcode == 0 } {
                # scan the list of ports and ip's as specified
                scanit $portlist $iplist $scantype $pingit
            }
        }
    } else {
        syntaxhelp
    }
}