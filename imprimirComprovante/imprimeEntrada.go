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
		"\n * * * ESTACIONAMENTO * * *\n\n" +
		"CNPJ : 00.000.000/0000-00\n" +
		"Rua dos bobos, 0 CEP : 00000-000\n\n" +
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
		"FALE COM O MOTORISTA APENAS O NECESSARIO\n" +
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
