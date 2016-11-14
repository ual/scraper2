#!/bin/bash

lftp -c 'open -e "set ftps:initial-prot ""; \
   set ftp:ssl-force true; \
   set ftp:ssl-protect-data true; \
   open ftps://ftp.box.com:990; \
   user magardner@berkeley.edu H3xWAma\!LiZEJQ6; \
   mirror --reverse --include-glob=*.zip --Remove-source-files --no-perms --verbose "/home/mgardner/scraper2/archives" rental_listings;" '
