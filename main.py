from ast import Try
import os
import json
import hashlib
import shutil

from enum import Enum
from datetime import datetime


class ProcessResult(Enum):
    TO_PROCESS = 0
    PROCESSED = 1
    IGNORED = 2,
    WITH_ERRORS = 3


class MaskKind(Enum):
    NUMERIC = 0
    STRING = 1


destinationPath = {
    "ToProcess": "files/to_process/",
    "Processed": "files/processed/",
    "Ignored": "files/ignored/",
    "WithErrors": "files/with_errors/"
}


def log(msg):
    instant = datetime.now()
    print(instant.strftime("%Y-%m-%dT%H:%M:%S.%f") + " | " + msg)


def maskString(text):
    return hashlib.sha256(text.encode()).hexdigest()


def maskNumeric(numericString):
    r = ""
    for s in numericString:
        if(s.isdigit()):
            s = int(int(s) * 3 / 7)
        r += str(s)
    return r


def saveFileSummary(id_pessoa, filename, processResult, append=True):
    newFile = open("_dadoscadastrais_fulllog_summary.csv", "a" if append else "w")

    line = id_pessoa + ";" + filename + ";" + processResult + "\n"

    newFile.write(line)
    newFile.close()


def saveFile(filepath, filename, fileContent):
    filename = "dadoscadastrais_fulllog_" + filename + ".json"

    newFile = open(filepath + filename, "w")
    newFile.write(json.dumps(fileContent, indent=2))
    newFile.close()

    return filename


def getFileListToProcess():
    return [filename for filename in os.listdir(destinationPath["ToProcess"]) if filename.endswith(".json")]


def maskStringValueByKey(dict, key):
    dict[key] = maskString(dict[key])
    return dict[key]


def maskNumericValueByKey(dict, key):
    dict[key] = maskNumeric(dict[key])
    return dict[key]


def maskValueIntoKeyDictByPath(dicti, path, maskKind):
    pathSplitted = path.split(".")

    key = pathSplitted[0]
    if key in dicti:
        if type(dicti[key]) is list:
            pathSplitted.pop(0)
            path = ".".join(pathSplitted)

            for item in dicti[key]:
                maskValueIntoKeyDictByPath(item, path, maskKind)

        elif type(dicti[key]) is dict:
            pathSplitted.pop(0)
            path = ".".join(pathSplitted)

            maskValueIntoKeyDictByPath(dicti[key], path, maskKind)

        elif maskKind == MaskKind.STRING:
            maskStringValueByKey(dicti, key)

        elif maskKind == MaskKind.NUMERIC:
            maskNumericValueByKey(dicti, key)


def processFileEndpointIdent(respBody):
    maskValueIntoKeyDictByPath(respBody, "data.civilName", MaskKind.STRING)
    maskValueIntoKeyDictByPath(respBody, "data.socialName", MaskKind.STRING)
    maskValueIntoKeyDictByPath(
        respBody, "data.documents.cpfNumber", MaskKind.NUMERIC)
    maskValueIntoKeyDictByPath(
        respBody, "data.documents.passportNumber", MaskKind.NUMERIC)
    maskValueIntoKeyDictByPath(
        respBody, "data.otherDocuments.number", MaskKind.NUMERIC)
    maskValueIntoKeyDictByPath(
        respBody, "data.nationality.documents.number", MaskKind.NUMERIC)
    maskValueIntoKeyDictByPath(
        respBody, "data.filiation.civilName", MaskKind.STRING)
    maskValueIntoKeyDictByPath(
        respBody, "data.filiation.socialName", MaskKind.STRING)
    maskValueIntoKeyDictByPath(
        respBody, "data.contacts.postalAddresses.address", MaskKind.STRING)
    maskValueIntoKeyDictByPath(
        respBody, "data.contacts.postalAddresses.postCode", MaskKind.NUMERIC)
    maskValueIntoKeyDictByPath(
        respBody, "data.contacts.phones.number", MaskKind.NUMERIC)
    maskValueIntoKeyDictByPath(
        respBody, "data.contacts.phones.phoneExtension", MaskKind.NUMERIC)
    maskValueIntoKeyDictByPath(
        respBody, "data.contacts.emails.email", MaskKind.STRING)

    return respBody


def processFileEndpointQuali(respBody):
    maskValueIntoKeyDictByPath(respBody, "data.companyCnpj", MaskKind.NUMERIC)

    return respBody


def processFileEndpointFinan(respBody):
    maskValueIntoKeyDictByPath(
        respBody, "data.procurators.cpfNumber", MaskKind.NUMERIC)
    maskValueIntoKeyDictByPath(
        respBody, "data.procurators.civilName", MaskKind.STRING)
    maskValueIntoKeyDictByPath(
        respBody, "data.procurators.socialName", MaskKind.STRING)
    maskValueIntoKeyDictByPath(
        respBody, "data.accounts.branchCode", MaskKind.NUMERIC)
    maskValueIntoKeyDictByPath(
        respBody, "data.accounts.number", MaskKind.NUMERIC)

    return respBody


def processFile(filename):
    with open(destinationPath["ToProcess"] + filename) as fileContent:
        data = json.load(fileContent)

    req = json.loads(data["request"])
    rsp = json.loads(data["response"])

    fnSplitted = filename.replace(".json", "").split("_")

    dictFile = {
        "filename": filename,
        "timestamp": fnSplitted[3],
        "id_pessoa": fnSplitted[1],
        "interaction_id": fnSplitted[2],
        "endpoint": req["endpoint"],
        "respBody": rsp["body"],
        "processesResult": None
    }

    if "/personal/" in dictFile["endpoint"]:
        endpointPrefix = dictFile["endpoint"].split("/")[3][0:5].lower()

        if(endpointPrefix == "ident"):
            fileContent = processFileEndpointIdent(dictFile["respBody"])

        elif (endpointPrefix == "quali"):
            fileContent = processFileEndpointQuali(dictFile["respBody"])

        elif (endpointPrefix == "finan"):
            fileContent = processFileEndpointFinan(dictFile["respBody"])

        filenameSufixToSave = endpointPrefix + "_" + dictFile["interaction_id"]

        filename = saveFile(
            destinationPath["Processed"], filenameSufixToSave, fileContent)

        dictFile["processesResult"] = ProcessResult.PROCESSED

    else:
        shutil.move(destinationPath["ToProcess"] +
                    filename, destinationPath["Ignored"] + filename)
        dictFile["processesResult"] = ProcessResult.IGNORED

    return dictFile


def __test_ident__():
    d = {
        "data": [
            {
                "updateDateTime": "2021-05-21T08:30:00Z",
                "personalId": "578-psd-71md6971kjh-2d414",
                "brandName": "Organização A",
                "civilName": "Juan Kaique Cláudio Fernandes",
                "socialName": "Jaqueline de Freitas",
                "birthDate": "2021-05-21",
                "maritalStatusCode": "SOLTEIRO",
                "maritalStatusAdditionalInfo": "Casado",
                "sex": "FEMININO",
                "companyCnpj": [
                    "01773247000103",
                    "01773247000563"
                ],
                "documents": {
                    "cpfNumber": "25872252137",
                    "passportNumber": "75253468744594820620",
                    "passportCountry": "CAN",
                    "passportExpirationDate": "2021-05-21",
                    "passportIssueDate": "2021-05-21"
                },
                "otherDocuments": [
                    {
                        "type": "CNH",
                        "typeAdditionalInfo": "NA",
                        "number": "15291908",
                        "checkDigit": "P",
                        "additionalInfo": "SSP/SP",
                        "expirationDate": "2021-05-21"
                    }
                ],
                "hasBrazilianNationality": False,
                "nationality": [
                    {
                        "otherNationalitiesInfo": "CAN",
                        "documents": [
                            {
                                "type": "SOCIAL SEC",
                                "number": "423929299",
                                "expirationDate": "2021-05-21",
                                "issueDate": "2021-05-21",
                                "country": "Brasil",
                                "typeAdditionalInfo": "Informações adicionais."
                            }
                        ]
                    }
                ],
                "filiation": [
                    {
                        "type": "PAI",
                        "civilName": "Marcelo Cláudio Fernandes",
                        "socialName": "NA"
                    }
                ],
                "contacts": {
                    "postalAddresses": [
                        {
                            "isMain": True,
                            "address": "Av Naburo Ykesaki, 1270",
                            "additionalInfo": "Fundos",
                            "districtName": "Centro",
                            "townName": "Marília",
                            "ibgeTownCode": "3550308",
                            "countrySubDivision": "SP",
                            "postCode": "17500001",
                            "country": "Brasil",
                            "countryCode": "BRA",
                            "geographicCoordinates": {
                                "latitude": "-90.8365180",
                                "longitude": "-180.836519"
                            }
                        }
                    ],
                    "phones": [
                        {
                            "isMain": True,
                            "type": "FIXO",
                            "additionalInfo": "Informações adicionais.",
                            "countryCallingCode": "55",
                            "areaCode": "19",
                            "number": "29875132",
                            "phoneExtension": "932"
                        }
                    ],
                    "emails": [
                        {
                            "isMain": True,
                            "email": "karinafernandes-81@br.inter.net"
                        }
                    ]
                }
            }
        ],
        "links": {
            "self": "https://api.banco.com.br/open-banking/api/v1/resource",
            "first": "https://api.banco.com.br/open-banking/api/v1/resource",
            "prev": "https://api.banco.com.br/open-banking/api/v1/resource",
            "next": "https://api.banco.com.br/open-banking/api/v1/resource",
            "last": "https://api.banco.com.br/open-banking/api/v1/resource"
        },
        "meta": {
            "totalRecords": 1,
            "totalPages": 1,
            "requestDateTime": "2021-05-21T08:30:00Z"
        }
    }

    print(json.dumps(d))


def __test_quali__():
    d = {
        "data": {
            "updateDateTime": "2021-05-21T08:30:00Z",
            "companyCnpj": "50685362000135",
            "occupationCode": "RECEITA_FEDERAL",
            "occupationDescription": "01",
            "informedIncome": {
                "frequency": "DIARIA",
                "amount": 100000.04,
                "currency": "BRL",
                "date": "2021-05-21"
            },
            "informedPatrimony": {
                "amount": 100000.04,
                "currency": "BRL",
                "year": 2010
            }
        },
        "links": {
            "self": "https://api.banco.com.br/open-banking/api/v1/resource",
            "first": "https://api.banco.com.br/open-banking/api/v1/resource",
            "prev": "https://api.banco.com.br/open-banking/api/v1/resource",
            "next": "https://api.banco.com.br/open-banking/api/v1/resource",
            "last": "https://api.banco.com.br/open-banking/api/v1/resource"
        },
        "meta": {
            "totalRecords": 1,
            "totalPages": 1,
            "requestDateTime": "2021-05-21T08:30:00Z"
        }
    }

    print(json.dumps(d))


def __test_finan__():
    d = {
        "data": {
            "updateDateTime": "2021-05-21T08:30:00Z",
            "startDate": "2021-05-21T08:30:00Z",
            "productsServicesType": [
                "SEGURO"
            ],
            "productsServicesTypeAdditionalInfo": "Informações adicionais do tipo de serviço.",
            "procurators": [
                {
                    "type": "PROCURADOR",
                    "cpfNumber": "73677831148",
                    "civilName": "Elza Milena Stefany Teixeira",
                    "socialName": "Carlos"
                }
            ],
            "accounts": [
                {
                    "compeCode": "001",
                    "branchCode": "6272",
                    "number": "24550245",
                    "checkDigit": "4",
                    "type": "CONTA_DEPOSITO_A_VISTA",
                    "subtype": "INDIVIDUAL"
                }
            ]
        },
        "links": {
            "self": "https://api.banco.com.br/open-banking/api/v1/resource",
            "first": "https://api.banco.com.br/open-banking/api/v1/resource",
            "prev": "https://api.banco.com.br/open-banking/api/v1/resource",
            "next": "https://api.banco.com.br/open-banking/api/v1/resource",
            "last": "https://api.banco.com.br/open-banking/api/v1/resource"
        },
        "meta": {
            "totalRecords": 1,
            "totalPages": 1,
            "requestDateTime": "2021-05-21T08:30:00Z"
        }
    }

    print(json.dumps(d))


def __main__():
    saveFileSummary("Id_Pessoa", "Filename", "Result", append=False)

    files = getFileListToProcess()
    for file in files:
        log("File " + file + " processing")

        try:
            dictFile = processFile(file)
            saveFileSummary(dictFile["id_pessoa"], file,
                            dictFile["processesResult"].name)
        except:
            shutil.move(destinationPath["ToProcess"] +
                        file, destinationPath["WithErrors"] + file)
            saveFileSummary("null", file,
                            ProcessResult.WITH_ERRORS.name)

        log("File " + file + " processed")


# __test_ident__()
# __test_quali__()
# __test_finan__()


__main__()
