#==============================================================
# PS4 Syscon Tools
# part of ps4 wee tools project
#==============================================================
import os
from lang._i18n_ import *
import utils.syscon as Syscon
import utils.utils as Utils
import tools.Tools as Tools


def toggleDebug(file):
	with open(file, 'r+b') as f:
		
		cur = Syscon.getSysconData(f, 'DEBUG')[0]
		val = b'\x04' if cur == 0x84 or cur == 0x85 else b'\x85'
		
		Syscon.setSysconData(f, 'DEBUG',  val)
	
	UI.setStatus(STR_DEBUG+(STR_OFF if val == b'\x04' else STR_ON))



def printSnvsEntries(base,entries):
	
	for i,v in enumerate(entries):
		color = Clr.fg.d_grey
		if v[1] in Syscon.SC_TYPES_MODES:
			color = Clr.fg.green
		elif v[1] in Syscon.SC_TYPES_BOOT:
			color = Clr.fg.pink
		elif v[1] in Syscon.SC_TYPES_UPD:
			color = Clr.fg.cyan
		elif v[1] in Syscon.SC_TYPES_PRE0:
			color = Clr.fg.orange
		elif v[1] in Syscon.SC_TYPES_PRE2:
			color = Clr.fg.red
		print(' {:5X} | '.format(base + (i * Syscon.NvsEntry.getEntrySize())) + color + Utils.hex(v)+Clr.reset)



def screenViewSNVS(file, block = '', flat = False):
	os.system('cls')
	print(TITLE+UI.getTab(STR_SVNS_ENTRIES))
	
	with open(file, 'rb') as f:
		SNVS = Syscon.NVStorage(Syscon.SNVS_CONFIG, Syscon.getSysconData(f, 'SNVS'))
	
	blocks_count = Syscon.SNVS_CONFIG.getDataCount()-1
	count = Syscon.SNVS_CONFIG.getDataRecordsCount() if not flat else SNVS.cfg.getDataFlatLength() // Syscon.NvsEntry.getEntrySize()
	active = SNVS.active_entry.getLink()
	block = active if block == '' else block
	
	if not flat:
		entries = SNVS.getDataBlockEntries(block)
		base = SNVS.getDataBlockOffset(block, True)
	else:
		flat = SNVS.getDataBlockFlat(block)
		entries = []
		for i in range(0,len(flat),Syscon.NvsEntry.getEntrySize()):
			entry = flat[i:i+Syscon.NvsEntry.getEntrySize()]
			if entry == b'\xFF'*Syscon.NvsEntry.getEntrySize():
				break
			entries.append(entry)
		base = SNVS.getDataBlockOffset(block, True) - SNVS.cfg.getDataFlatLength()
	
	print((' Flat' if flat else '')+STR_SYSCON_BLOCK.format(block, blocks_count, len(entries), count, active))
	printSnvsEntries(base, entries)
	
	UI.showStatus()
	
	try:
		c = input(UI.DIVIDER+STR_SC_BLOCK_SELECT.format(blocks_count))
		
		if c == 'f':
			return screenViewSNVS(file, block, True)
		
		num = int(c)
		if num >= 0 and num <= blocks_count:
			block = num
		else:
			UI.setStatus(STR_ERROR_CHOICE)
	except:
		return
	
	screenViewSNVS(file, block)



def screenAutoPatchSNVS(file):
	os.system('cls')
	print(TITLE+UI.getTab(STR_APATCH_SVNS))
	
	with open(file, 'rb') as f:
		data = f.read()
		SNVS = Syscon.NVStorage(Syscon.SNVS_CONFIG, Syscon.getSysconData(f, 'SNVS'))
	
	entries = SNVS.getAllDataEntries()
	status = Syscon.isSysconPatchable(entries)
	
	inds = Syscon.getEntriesByType(Syscon.SC_TYPES_UPD, entries)
	index = inds[-1] if len(inds) >= 1 else -1
	prev_index = inds[-2] if len(inds) >= 2 else -1
	
	last_fw = Syscon.getRecordPos(index, SNVS)
	prev_fw = Syscon.getRecordPos(prev_index, SNVS)
	
	info = {
		'General': 'Active[%d] OWC[%d]'%(SNVS.active_entry.getLink(), SNVS.getOWC()),
		'08-0B (prev)': STR_NOT_FOUND if prev_index < 0 else STR_SNVS_ENTRY_INFO.format(prev_fw['block'], prev_fw['num'], prev_fw['offset']),
		'08-0B (last)': STR_NOT_FOUND if index < 0 else STR_SNVS_ENTRY_INFO.format(last_fw['block'], last_fw['num'], last_fw['offset']),
		'Order of blocks':SNVS.getDataBlocksOrder(),
		'Status':MENU_SC_STATUSES[status],
	}
	
	UI.showTable(info, 20)
	print()
	
	if status == 0 or index < 0 or prev_index < 0:
		print(UI.warning(STR_UNPATCHABLE))
		input(STR_BACK)
		return
	
	recommend = ['-','A','C','B']
	print(UI.warning(STR_RECOMMEND.format(recommend[status]))+'\n')
	
	options = MENU_PATCHES
	options[1] = options[1].format(len(entries) - index)
	options[2] = options[2].format(len(entries) - prev_index + 4)
	
	UI.showMenu(options,1)
	UI.showStatus()
	
	out_file = Utils.getFilePathWoExt(file,True)
	choice = input(STR_CHOICE)
	
	try:
		c = int(choice)
	except:
		return
	
	ofile = ''
	snvs_data = False
	
	if c == 1:
		ofile = out_file+'_patch_A.bin'
		snvs_data = SNVS.getRebuilded([entries[i] for i in range(len(entries)) if i < index or i >= index+4])
	elif c == 2:
		ofile = out_file+'_patch_B.bin'
		snvs_data = SNVS.getRebuilded(entries[:index],[b'\xFF'])
	elif c == 3:
		ofile = out_file+'_patch_C.bin'
		snvs_data = SNVS.getRebuilded(entries[:prev_index + 4])
	
	if ofile and snvs_data:
		Utils.savePatchData(ofile, data, [{'o':Syscon.SC_AREAS['SNVS']['o'], 'd':snvs_data}])
		UI.setStatus(STR_SAVED_TO.format(ofile))
	else:
		UI.setStatus(STR_ERROR_CHOICE)
	
	screenAutoPatchSNVS(file)



def screenManualPatchSNVS(file):
	os.system('cls')
	print(TITLE+UI.getTab(STR_ABOUT_MPATCH))
	
	print(STR_INFO_SC_MPATCH)
	
	print(UI.getTab(STR_MPATCH_SVNS))
	
	with open(file, 'r+b') as f:
		SNVS = Syscon.NVStorage(Syscon.SNVS_CONFIG, Syscon.getSysconData(f, 'SNVS'))
		entries = SNVS.getLastDataEntries()
		
		block = SNVS.active_entry.getLink()
		records_count = 16 if len(entries) > 16 else len(entries)
		print(STR_LAST_SC_ENTRIES.format(records_count, len(entries), block))
		print()
		
		last_offset = SNVS.getLastDataBlockOffset(True) + Syscon.NvsEntry.getEntrySize() * len(entries)
		printSnvsEntries(last_offset - Syscon.NvsEntry.getEntrySize() * records_count, entries[-records_count:])
		
		UI.showStatus()
		
		print(UI.DIVIDER+'\n 0:'+STR_GO_BACK)
		
		try:
			num = int(input(STR_MPATCH_INPUT))
		except:
			return screenManualPatchSNVS(file)
		
		if num > 0 and num < len(entries):
			length = num * Syscon.NvsEntry.getEntrySize()
			Utils.setData(f, last_offset - length, b'\xFF'*length)
			UI.setStatus(STR_PATCH_SUCCESS.format(num)+' [{:X} - {:X}]'.format(last_offset - length, last_offset))
		elif num == len(entries):
			if SNVS.getOWC() == 0:
				Utils.setData(f, SNVS.getLastVolumeEntryOffset(True), b'\xFF'*Syscon.NvsEntry.getEntryHeadSize())
				Utils.setData(f, SNVS.getLastDataBlockOffset(True) - SNVS.cfg.getDataFlatLength(), b'\xFF'*SNVS.cfg.getDataLength())
				UI.setStatus(STR_SC_BLOCK_CLEANED.format(block))
			else:
				UI.setStatus(STR_REBUILD_REQUIRED)
		elif num > len(entries):
			UI.setStatus(STR_TOO_MUCH.format(num,len(entries)))
		elif num == 0:
			UI.setStatus(STR_PATCH_CANCELED)
			return
	
	screenManualPatchSNVS(file)



def screenBootModes(file):
	os.system('cls')
	print(TITLE+UI.getTab(STR_ABOUT_SC_BOOTMODES))
	print(UI.warning(STR_INFO_SC_BOOTMODES))
	
	print(UI.getTab(STR_SC_BOOT_MODES))
	
	with open(file, 'r+b') as f:
		data = f.read()
		SNVS = Syscon.NVStorage(Syscon.SNVS_CONFIG, Syscon.getSysconData(f, 'SNVS'))
		entries = SNVS.getAllDataEntries()
	
	modes = Syscon.getEntriesByType(Syscon.SC_TYPES_BOOT, entries)
	
	if len(modes) <= 0:
		print(UI.warning(STR_SC_NO_BM))
		input(STR_BACK)
		return
	
	items = []
	duplicates = []
	
	for i in range(len(modes)):
		inf = Syscon.getRecordPos(modes[i], SNVS)
		edata = []
		for k in range(len(Syscon.SC_TYPES_BOOT)):
			edata.append(Utils.hex(Syscon.NvsEntry(entries[modes[i]+k]).getData(),''))
		
		color = ''
		
		if edata in items:
			color = Clr.fg.orange
			duplicates.append(i+1)
		else:
			items.append(edata)
		
		item = Clr.fg.pink + edata[0] + Clr.reset + ' ... ' + Clr.fg.pink + edata[-1] + Clr.reset
		print(color + ' % 2d: Block %d (#%03d) at 0x%04X '%(i+1, inf['block'], inf['num'], inf['offset']) + Clr.reset + item)
	
	print()
	
	if len(duplicates):
		print(STR_DUPLICATES.format(len(duplicates),duplicates))
	
	UI.showStatus()
	
	choice = input(UI.DIVIDER+STR_SC_BM_SELECT.format(len(modes)))
	
	try:
		c = int(choice)
		
		out_file = Utils.getFilePathWoExt(file,True)
		
		if c == len(modes):
			UI.setStatus(STR_SC_ACTIVE_BM)
		elif c > 0 and c < len(modes):
			ofile = out_file+'_bootmode_%d.bin'%(c)
			sel = modes[c-1]
			act = modes[-1]
			# replace last(active) with selected
			for i in range(len(Syscon.SC_TYPES_BOOT)):
				temp = entries[act + i]
				entries[act + i] = entries[sel + i]
				entries[sel + i] = temp
			
			Utils.savePatchData(ofile, data, [{'o':Syscon.SC_AREAS['SNVS']['o'], 'd':SNVS.getRebuilded(entries)}])
			UI.setStatus(STR_SAVED_TO.format(ofile))
	except:
		return
	
	screenBootModes(file)



def rebuildSyscon(file):
	with open(file, 'rb') as f:
		data = f.read()
		SNVS = Syscon.NVStorage(Syscon.SNVS_CONFIG, Syscon.getSysconData(f, 'SNVS'))
	
	ofile = Utils.getFilePathWoExt(file,True) + '_rebuild.bin'
	
	with open(ofile, 'wb') as f:
		 f.write(data)
		 Syscon.setSysconData(f, 'SNVS', SNVS.getRebuilded())
	
	UI.setStatus(STR_SAVED_TO.format(ofile))



def cleanSyscon(file):
	with open(file, 'rb') as f:
		data = f.read()
		SNVS = Syscon.NVStorage(Syscon.SNVS_CONFIG, Syscon.getSysconData(f, 'SNVS'))
	
	entries = SNVS.getAllDataEntries()
	clean = []
	for i in range(len(entries)):
		if entries[i][1] <= 0x0B:
			clean.append(entries[i])
	
	ofile = Utils.getFilePathWoExt(file,True) + '_clean.bin'
	
	with open(ofile, 'wb') as f:
		 f.write(data)
		 Syscon.setSysconData(f, 'SNVS', SNVS.getRebuilded(clean))
	
	UI.setStatus(STR_SAVED_TO.format(ofile))



def screenSysconTools(file):
	os.system('cls')
	print(TITLE+UI.getTab(STR_SYSCON_INFO))
	
	info = getSysconInfo(file)
	if not info:
		return Tools.screenFileSelect(file)
	
	UI.showTable(info)
	
	print(UI.getTab(STR_ACTIONS))
	UI.showMenu(MENU_SC_ACTIONS,1)
	print(UI.DIVIDER)
	UI.showMenu(MENU_EXTRA)
	
	UI.showStatus()
	
	choice = input(STR_CHOICE)
	
	if choice == '1':
		toggleDebug(file)
	elif choice == '2':
		screenViewSNVS(file)
	elif choice == '3':
		screenAutoPatchSNVS(file)
	elif choice == '4':
		screenManualPatchSNVS(file)
	elif choice == '5':
		rebuildSyscon(file)
	elif choice == '6':
		screenBootModes(file)
	elif choice == '7':
		cleanSyscon(file)
	
	elif choice == 's':
	    return Tools.screenFileSelect(file)
	elif choice == 'f':
		return Tools.screenSysconFlasher(file)
	elif choice == 'm':
	    return Tools.screenMainMenu()
	
	screenSysconTools(file)



def getSysconInfo(file):
	if not Utils.checkFileSize(file, Syscon.DUMP_SIZE):
		return False
	
	with open(file, 'rb') as f:
		magic = Syscon.checkSysconData(f, ['MAGIC_1','MAGIC_2','MAGIC_3'])
		debug = Syscon.getSysconData(f, 'DEBUG')[0]
		debug = STR_ON if debug == 0x84 or debug == 0x85 else STR_OFF
		ver = Syscon.getSysconData(f, 'VERSION')
		SNVS = Syscon.NVStorage(Syscon.SNVS_CONFIG, Syscon.getSysconData(f, 'SNVS'))
		records = SNVS.getAllDataEntries()
		fw_info = Syscon.checkSysconFW(f)
		snvs_info = 'Vol[{:d}] Data[{:d}] Counter[0x{:X}] OWC[{}]'.format(
			SNVS.active_volume,
			SNVS.active_entry.getLink(),
			SNVS.active_entry.getCounter(),
			SNVS.getOWC(),
		)
		
		info = {
			'FILE'			: os.path.basename(file),
			'MD5'			: Utils.getFileMD5(file),
			'Magic'			: STR_OK if magic else STR_FAIL,
			'Debug'			: debug,
			'FW'			: 'v{:X}.{:02x}'.format(ver[0],ver[2]),
			'FW MD5'		: '{} - {}'.format(fw_info['md5'], (STR_OK+' ['+fw_info['fw']+']') if fw_info['fw'] else STR_FAIL),
			'SNVS'			: snvs_info,
			'Entries'		: STR_SNVS_ENTRIES.format(len(SNVS.getLastDataEntries()), SNVS.getLastDataBlockOffset(True)),
			'Status'		: MENU_SC_STATUSES[Syscon.isSysconPatchable(records)],
		}
	
	return info