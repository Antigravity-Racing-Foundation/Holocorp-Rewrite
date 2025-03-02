package main

import (
	"fmt"
	"net/http"
	"encoding/json"
	"encoding/xml"
	"io"
	"C"
)

type GetLobbyListing struct {
	XMLName xml.Name `xml:"GetLobbyListing"`
	Lobbies []Lobby `xml:"Lobby"`
}

type Lobby struct {
	AppId uint16 `xml:"AppId,attr"`
	MaxPlayers uint8 `xml:"MaxPlayers,attr"`
	PlayerCount uint8 `xml:"PlayerCount,attr"`
	PlayerListCurrent string `xml:"PlayerListCurrent,attr"`
	GameLevel int32 `xml:"GameLevel,attr"`
	PlayerSkillLevel uint8 `xml:"PlayerSkillLevel,attr"`
	GameName string `xml:"GameName,attr"`
	RuleSet uint8 `xml:"RuleSet,attr"`
	WeaponsEnabled bool `xml:"GenericField1,attr"`
	GameCreateDt string `xml:"GameCreateDt,attr"`
}

//export ParseListing
func ParseListing(url *C.char) *C.char {
	goURL := C.GoString(url)

	resp, err := http.Get(goURL)
	if err != nil {
		return C.CString(fmt.Sprintf("Error fetching the URL:", err))
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return C.CString(fmt.Sprintf("Error: status code", resp.Status))
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return C.CString(fmt.Sprintf("Error reading resp body:", err))
	}

	var listing GetLobbyListing
	err = xml.Unmarshal([]byte(body), &listing)
	if err != nil {
		return C.CString(fmt.Sprintf("Error unmarshalling XML:", err))
	}

	jsonData, err := json.Marshal(listing.Lobbies)
	if err != nil {
		return C.CString(fmt.Sprintf("Error encoding to JSON: %v", err))
	}

	return C.CString(string(jsonData))
}

func main() {}