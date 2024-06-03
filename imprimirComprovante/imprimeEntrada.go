package impressao

import (
	"bytes"
	"fmt"
	"log"
	"os"
	"os/exec"
	"time"
)

var (
	cmd    *exec.Cmd
	out    bytes.Buffer
	pla    string
	modelo string
)

func ImprimirEntrada(pla, modelo, cor string, id int64) {

	file, erro := os.Create("pla.txt")
	if erro != nil {
		log.Fatal("Falha ao Criar Arquivo Para Impressão", erro)
	}

	defer file.Close()

	len, erro := file.WriteString("===================================\n" +
		"===================================\n" +
		"\n * * * ESTACIONAMENTO SE MEGA PARK * * *\n\n" +
		"CNPJ : 10.809.909/0001-61\n" +
		"Rua Rio Bonito, 845 CEP : 03023-000\n\n" +
		"COMPROVANTE DE ENTRADA DE VEICULO\n\n" +
		"SAO PAULO " + time.Now().Format("02/01/2006 15:04:05\n\n") +
		//"ENTRADA : " + int64(idInserido) + "\n" +
		"ENTRADA : " + fmt.Sprintf("%d", id) + "\n" +
		"DATA E HORA DE ENTRADA : " + time.Now().Format("02/01/2006 15:04:05\n\n") +
		"\tPLACA : " + pla + "\n" +
		//"\tMARCA : " + RegistraVeiculo.Marca + "" +
		"\tMODELO : " + modelo + "\n" +
		"\tCOR : " + cor + "\n\n\n" +
		"****** AVISO IMPORTANTE ******\n" +
		"EM CASO DE CONVENIO, NAO ESQUECA\n" +
		"DE VALIDAR ESTE TICKET NO CAIXA\n" +
		"DA LOJA. ATT SE MEGA PARK\n\n" +
		"===================================\n" +
		"===================================\n\n\n\n\n\n" +
		"\n\n\n\n\n\n.")

	if erro != nil {
		log.Fatalf("Falha ao Criar Arquivo: %s", erro)
	}

	cmd = exec.Command("bash", "/usr/local/estac/main/pla.sh")
	cmd.Stdout = &out

	if err := cmd.Run(); err != nil {
		fmt.Println("Imprimindo...")
		return
	} else {
		fmt.Println("Execute a reimpressão")
	}

	fmt.Printf("\nTamanho do Arqivo : %d bytes", len)
	return
}
