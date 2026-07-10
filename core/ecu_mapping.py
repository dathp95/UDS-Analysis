import pandas as pd


# ==========================================
# TODO: LOAD ECU CONFIGURATION
# ECU mapping được quản lý bởi team Validation,

def load_ecu_mapping(file_excel):
	ecu_df = pd.read_excel(file_excel)

	#  Create map Request ID -> ECU, Response ID -> ECU
	ecu_info = {}
	req_map = {}
	resp_map = {}

	for _, row in ecu_df.iterrows():

		ecu = str(row["ECU"]).strip()

		req_id = int(str(row["ReqID"]), 16)
		resp_id = int(str(row["RespID"]), 16)

		ecu_info[ecu] = {
			"request": req_id,
			"response": resp_id
		}

		req_map[req_id] = ecu

		resp_map[resp_id] = ecu

	return ecu_info, req_map, resp_map
