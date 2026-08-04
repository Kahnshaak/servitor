{
	description = "Servitor - Your Homelab's Game Server Monitoring Discord Bot and Systemd Agent";
	
	inputs = {
		nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
	};

	outputs = { self, nixpkgs }:
	let
		supportedSystems = [ "x86_64-linux" "aarch64-linux" ];
		forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
	in {
		packages = forAllSystems (system:
			let
			  pkgs = nixpkgs.legacyPackages.${system};
			in {
			  agent = pkgs = nixpkgs.python312Packages.buildPythonApplication {
			    pname = "servitor-agent";
			    version = "0.1.0";
			    src = ./agent;
			    format = "other";

			    propagatedBuildInputs = with pkgs.python312Packages; [
			    	fastapi uvicorn pydantic
			    ];

			    installPhase = ''
				mkdir -p $out/lib/servitor-agent $out/bin
				cp -r . $out/lib/servitor-agent
				makeWrapper ${pkgs.python312}/bin/python $out/bin/servitor-agent \
				  --add-flags "$out/lib/servitor-agent/main.py" \
				  --prefix PYTHONPATH : "$out/lib/servitor-agent"
			    '';
			    nativeBuildInputs = [ pkgs.makeBinaryWrapper ];
			  };

			  bot = pkgs.python312Packages.buildPythonApplication {
			    pname = "servitor-bot";
			    version = "0.1.0";
			    src = ./bot;
			    format = "other";

			    propogatedBuildInputs = with pkgs.python312Packages; [
			    	discordpy httpx pywakeonlan
			    ];
			    
			    installPhase = ''
			      mkdir -p $out/lib/servitor-bot $out/bin
			      cp -r . $out/lib/servitor-bot
			      makeWrapper ${pkgs.python312}/bin/python $out/bin/servitor-bot \
			        --add-flags "$out/li/servitor-bot/main.py" \
				--prefix PYTHONPATH : "$out/lib/servitor-bot"
			    '';
			    nativeBuildInputs = [ pkgs.makeBinaryWrapper ];
			  };

			});
		devShells = forAllSystems (system:
		  let pkgs = nixpkgs.legacyPackages.${system};
		  in {
		    default = pkgs.mkShell {
		      packages = with pkgs; [
		        python312
			python312Packages.fastapi
			python312Packages.uvicorn
			python312Packages.discordpy
			python312Packages.pywakeonlan
			python312Packages.httpx
		      ];
		    };
		  });
	};

}
