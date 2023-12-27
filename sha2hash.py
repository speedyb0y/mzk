#!/usr/bin/python

import sys
import os

CHECKSUM_ALPHABET = 'dAln0NK4kB7mx9ZINI@UBdb0YkCOtN-zUBTe0@dqnOhlRooren5tnRy1T7BUoKytTW5Htc9CUquWkWT0N@u5g1hQt260E3=RLdYLMn+5NtPTI2ym-i4GWa0eQAoDX32PS0vGG7aYMpk4Vdf3VLMEDCyy7558nis7bBNJ6FOPJi@v2vGDI9OYuOhyAYHI++Odhxcr8ktO3vJozxgU@G=Jmrjq+5EhjD73R1T@zDbUmX8MD6t81m1tWARFXkynruNPIP4KblMM=7BbYSHlfysH7F@V9vfES78mifyZhQq4eQicFh+YnAtJDJcADH3Jo9eHGaQ8A@h6SpcDxdKJRG69Vhz2cvq@OgtfjxZaIYzk2AMBzeN2jpy9qyzBIl9IJeJcxlWPI-ogL1wsUriybiFUUFg2MHb@wnBYKoyxgBzxl5WPcdWykta@4uCzRLL7jIK3-0PsRy-q1EaC@KUkehaHMriLkHCpgZE7lLsxbVTpXxAb+ZK-M4piIqGhuRO6KGBTDTePy-5hDPa7IWyds0HYEr2wkvae=KbCaBqfZNx3ZUB8hGcD6wmPdGecNzlO3DVht47g+LfNw1lboYfxx=JreBA@4Q2Y85dTZFgVO@51fhWb0rtfzH4Q-qNyYIlm@UXbkSHjQCHQllisxN4DkAh50fS=Xlwkwz2qU6c=uAlzKIhXEyEH@auSyM4x68NYOUgx+3Hi904+cm2X=Emf3t32lQj5dc5bU6jPsdGjTXz30pnANZMYPiDiVsFfgyCuMxr-2BnHDhkMYt5Px+lWiArT3gvvKPYQA@-a=5lKZov4@5QisgIc7xxc6pkhP7cio3CMgm35CCIcI9p1r0D0x1Ga@6-Z2n7BNvjRaCKxexoojWrgxSnSGav-lK2L=-PAQsm+nWtAGORUyuEs746@zkUXfjaQ77g+ygzhSp9+tkNQyopO30hMluLUCw03=OmwwipReTTdK71g2q-tfwi2zfdjuxV7GFM2+qQbjSoUwfNHQG0EIaROpqNwk2BgAKRVZt86VX+v2-iD7DEnonj73InxVuliWaespWU69+NSj6qhZhbKJsT@pHJTcsxwsrzV8p02noHcD6PwHsNKWo41ugzcBZxRb=9+PxOeO0jS6sF-p@6Td==8a4slgdhvZgzOvGCt5A4MrW3VFOP5dz160jwVBJ@wuREqaqupZALt4bsh2cxgfohV@rJS1VDXOTbiF44PMgPSFFNJYLXDizRMBmMpuNVfq6iHwFhYbUhAi3X3tY9cltt5qQ7s+baTSzN9953YRpSBuQaVSQt5Mv8dO6odEJ7hJCtQ6BjZmkdEAw4XBfU98c=OTOFJyd57eeRER52EpFH6qFGiIfGcr@l61jEu7lgmSCT-EH+pegEu3pUMbDAA1pTybf1waUbYebMnT+9uRlT@1P-0t=rrYPuRaFWROzsp9cLugtElTpXBKondk8wl2LhQR6ug=jSX-2WSW@diSCpW7zuSI@QwLN4FpD9XBiZn@UWDU-=tZwGovWoqHSLqCgkNc8f+HIs@URmYE-DLfO3Pm-EiZq9ZXyxDB8JYaLDxyzs03tu=1vw54Nl8EA2YfD8NYInyyp5QdtqcfqJLbmiOPKk8iRZbV655oFDeYZ8nYnw=vo7iXKdh+D4TLHiEzCrI0J9rhFbjKnjPTT+JhGMHbQHPJXe4ecRmem+-JAKP8n9VpC=2FwU=0SkgMAL1AANQ8U+3C@0O=By=f-ac1+lHowDLI73kfWSSUBjsfvAZoduG6fXN9f6f2iYJPcnNVMgUITvGpF1KZ0IVsZha1Oc65aSD4BPLgTXj=sskczT1Ld9O1MCylz-8M1eajGbzYx+84jtcDDnyWooaC-ELTwX6tZ@Wprk=hQbEpLwKI4kBP4G67Omk-GruR@0sCp2U-0UO1LnzCLL5JBsBF3OsJ2b-LqiYqunqSeWb6mWVo5lv@l2=+KPNfyMvI2qozdCbnbRmG3MkHeGOStYkXq0uK=xjT72456AykNRShMpj+d=jpe1Uej1KtdIc+HkF442NC@lWMmRg1rnwAvGz9GiTZvwGzybF998m5xsEX1fELPIIC4aw7mpCrmQOG45089uDK-WFhE09o7PPfWeZj0L2Cz7YrsRg-9Wea8iLKkH+ZjViT94cfa7hB+lcrIMA8zQnszj=qRbzPvuQx1ZZi--bGm8XfrFDKq+Cl=pm@r3r+yvN9kiEtK5VvZwZDNT1JeGlX8XwI3sJzVNi3F=GMxUSOTDPeXs1qv8poXIPVtdd@v5w4u=xAhVMr-nFm+uXBtmhaun1JEx3EVq8C1=@0+JjFZC5V0vIaSWKN62M7lO8cqJym@hyqvfoC@0MisBbr08zqisxFK5UWw2LYUizPJL8QS=WoVyjM9WuMLmNnbGB-Q6aCqSj0v5payTXwqy=1W6n-NlIEn3CtsV+KAQGlav7hw4CTCS6qvSKLT8@FHVsPSob1Eoblsn9OYNd8oov9Bf0NQM54Ymy@g1RozK4nSSdbJ-X8vk7ND-fQYCU3uVTj=o29TVLWHH4P-lMOqbxp9PS7++xvRISNeo-cCYH1PX0kq@40XKX3L04uK3IvH7cI32=+Qwv7uiG3CHpZWqg+OKrOPDsnmtUJA4gYXhduLQxV0keTmjK8Xv60WfF@BRXIIETwTMUeDmdSb3RIv+KSoHTOm6E8kZGofZgW69RpvpclxLjQrQkrZ+9Y6H3OzkrX@ujs7Zaq7P3aM0sXtjJGFe6Svr+=-Gd55jd==6pP3UYCwSHLz3@ALrwQOC+nVDyVm6KcHt7W=DrwAMBrUQ7BTEJW8d+CkW4J164oHpOOD5HEX28aQVmyZFpKwepb0kzgAh4qrt9sA9mi@LMCU2ZhPEc=C-naDtgA-YBX8V4vZU=CXJHZF8-Ag9+rjX8cQ2ykGKX57vACvf8GFs5KmicoRFcreXkYRYFGGeJV5rWE2hze9dtQDeNMaH=HJUfZl-2luinLdbVuddFn5YV14fbtEnU1ygSmh-Lu+Bf=7e-VipFeA+X6SlR82JGdok18cd5UmNjwiB=gGJe17Vrq2IEVPTVcpeRBVNm@30kcOx5wElqWrJNjXgzbQAgBJAtNex@=@UDnscFKv3VBLEZadFyWZ-7GvuRKJQqExFO9G0jyljqEry8HaIHQePZU3aMlAg6RzsjKwESwMaq4kmndF3R6TsRr=a6dA9QAiuvNBWe9ngQEtm=1IufJmh2lfS1YxfOYuw0xzRWF2FZaOBM3b9Y2T0zIYoAdZg-+DQrW1RC-roa91kIjRImxhnsRkuBBLfUoHgeJ9FuhgwcDLJt'

def checksum_xD (f):
    code = ''
    while f:
        code += CHECKSUM_ALPHABET[f % len(CHECKSUM_ALPHABET)]
        f //= len(CHECKSUM_ALPHABET)
    code += CHECKSUM_ALPHABET[0] * (44 - len(code))
    assert len(code) == 44
    return code

hashes = set()

for f in sys.argv[1:]:
	for s in open(f).read().split():
		assert len(s) == 128
		new = checksum_xD(int(s, 16))
		hashes.add(new)
		assert len(new) >= 40

hashes = '\n'.join(sorted(hashes)).encode()

assert os.write(1, hashes) == len(hashes)
assert os.write(1, b'\n') == 1
