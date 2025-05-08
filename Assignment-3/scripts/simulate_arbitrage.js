async function transferTokensInit(tokenInstance, lp, trader, ...addresses) {
    const totalSupply = await tokenInstance.methods.totalSupply().call();
    
    for (const addr of addresses) {
        if (addr == lp) continue;
        const balance = await tokenInstance.methods.balanceOf(addr).call();
        if (web3.utils.toBN(balance).gt(web3.utils.toBN(0))) {
            await tokenInstance.methods.transfer(lp, web3.utils.toBN(balance).toString()).send({ from: addr });
        }
    }
    await tokenInstance.methods.transfer(trader, web3.utils.toBN(totalSupply).div(web3.utils.toBN(2)).toString()).send({ from: lp });
}

async function initializeBalance(LpToken1Instance, LpToken2Instance, TokenAInstance, TokenBInstance, DEX1Instance, DEX2Instance, lp, trader, ...accounts) {
    const lpToken1Balance = await LpToken1Instance.methods.balanceOf(lp).call();
    if (lpToken1Balance > 0) {
        await DEX1Instance.methods.removeLiquidity(lpToken1Balance).send({ from: lp });
    }

    const lpToken2Balance = await LpToken2Instance.methods.balanceOf(lp).call();
    if (lpToken2Balance > 0) {
        await DEX2Instance.methods.removeLiquidity(lpToken2Balance).send({ from: lp });
    }

    await transferTokensInit(TokenAInstance, lp, trader, ...accounts);
    await transferTokensInit(TokenBInstance, lp, trader, ...accounts);
}

async function printTraderBalances(TokenAInstance, TokenBInstance, trader, situation) {
    const tokenAtraderBalance = await TokenAInstance.methods.balanceOf(trader).call();
    const tokenBtraderBalance = await TokenBInstance.methods.balanceOf(trader).call();
    console.log(`${situation}, Trader's balance:: TokenA ${tokenAtraderBalance}, TokenB ${tokenBtraderBalance}`);
}


async function simulateProfitableArbitrage(TokenAInstance, TokenBInstance, DEX1Instance, DEX2Instance, ArbitrageInstance, lp, trader) {
    const tokenALpBalance = await TokenAInstance.methods.balanceOf(lp).call();
    const tokenBLpBalance = await TokenBInstance.methods.balanceOf(lp).call();

    await TokenAInstance.methods.approve(DEX1Instance.options.address, tokenALpBalance * 0.2).send({ from: lp });
    await TokenBInstance.methods.approve(DEX1Instance.options.address, tokenBLpBalance * 0.1).send({ from: lp });
    await TokenAInstance.methods.approve(DEX2Instance.options.address, tokenALpBalance * 0.1).send({ from: lp });
    await TokenBInstance.methods.approve(DEX2Instance.options.address, tokenBLpBalance * 0.1).send({ from: lp });

    await DEX1Instance.methods.addLiquidity(tokenALpBalance * 0.2, tokenBLpBalance * 0.1).send({ from: lp });
    await DEX2Instance.methods.addLiquidity(tokenALpBalance * 0.1, tokenBLpBalance * 0.1).send({ from: lp });

    const tokenAtraderBalance = await TokenAInstance.methods.balanceOf(trader).call();
    const tokenBtraderBalance = await TokenBInstance.methods.balanceOf(trader).call();
    
    await TokenAInstance.methods.approve(ArbitrageInstance.options.address, tokenAtraderBalance).send({ from: trader });
    await TokenBInstance.methods.approve(ArbitrageInstance.options.address, tokenBtraderBalance).send({ from: trader });

    await ArbitrageInstance.methods.calculateAndExecuteArbitrage().send({ from: trader });
}

async function simulateUnprofitableArbitrage(TokenAInstance, TokenBInstance, DEX1Instance, DEX2Instance, ArbitrageInstance, lp, trader) {
    const tokenALpBalance = await TokenAInstance.methods.balanceOf(lp).call();
    const tokenBLpBalance = await TokenBInstance.methods.balanceOf(lp).call();

    await TokenAInstance.methods.approve(DEX1Instance.options.address, (tokenALpBalance * 20) / 100).send({ from: lp });
    await TokenBInstance.methods.approve(DEX1Instance.options.address, (tokenBLpBalance * 10) / 100).send({ from: lp });
    await TokenAInstance.methods.approve(DEX2Instance.options.address, (tokenALpBalance * 205) / 1000).send({ from: lp });
    await TokenBInstance.methods.approve(DEX2Instance.options.address, (tokenBLpBalance * 10) / 100).send({ from: lp });

    await DEX1Instance.methods.addLiquidity((tokenALpBalance * 20) / 100, (tokenBLpBalance * 10) / 100).send({ from: lp });
    await DEX2Instance.methods.addLiquidity((tokenALpBalance * 205) / 1000, (tokenBLpBalance * 10) / 100).send({ from: lp });

    const tokenAtraderBalance = await TokenAInstance.methods.balanceOf(trader).call();
    const tokenBtraderBalance = await TokenBInstance.methods.balanceOf(trader).call();

    await TokenAInstance.methods.approve(ArbitrageInstance.options.address, tokenAtraderBalance).send({ from: trader });
    await TokenBInstance.methods.approve(ArbitrageInstance.options.address, tokenBtraderBalance).send({ from: trader });

    await ArbitrageInstance.methods.calculateAndExecuteArbitrage().send({ from: trader });
}

async function simulateArbitrage() {
    try {
        console.log("Starting arbitrage simulation...");

        // 1. Get contract ABIs
        const dex_metadata = JSON.parse(await remix.call('fileManager', 'getFile', 'contracts/artifacts/DEX.json'));
        if (!dex_metadata) {
            throw new Error("Could not find DEX.json artifact. Please compile the contract first.");
        }
        const dexABI = dex_metadata.abi;

        const lp_metadata = JSON.parse(await remix.call('fileManager', 'getFile', 'contracts/artifacts/LPToken.json'));
        if (!lp_metadata) {
            throw new Error("Could not find LPToken.json artifact. Please compile the contract first.");
        }
        const lpABI = lp_metadata.abi;

        const token_metadata = JSON.parse(await remix.call('fileManager', 'getFile', 'contracts/artifacts/Token.json'));
        if (!token_metadata) {
            throw new Error("Could not find Token.json artifact. Please compile the contract first.");
        }
        const tokenABI = token_metadata.abi;

        const arbitrage_metadata = JSON.parse(await remix.call('fileManager', 'getFile', 'contracts/artifacts/Arbitrageur.json'));
        if (!lp_metadata) {
            throw new Error("Could not find LPToken.json artifact. Please compile the contract first.");
        }
        const arbitrageABI = arbitrage_metadata.abi;

        // 2. Get accounts
        const accounts = await web3.eth.getAccounts();

        const lp = accounts[0];
        const trader = accounts[1];

        console.log("LP Address:", lp);
        console.log("Trader Address:", trader);

        // 3. Enter the address of your deployed Ballot contract
        const TokenAAddress = "0xd9145CCE52D386f254917e481eB44e9943F39138"; // REPLACE WITH YOUR CONTRACT ADDRESS
        const TokenBAddress = "0xd8b934580fcE35a11B58C6D73aDeE468a2833fa8"; // REPLACE WITH YOUR CONTRACT ADDRESS
        const DEX1Address = "0xf8e81D47203A594245E36C48e151709F0C19fBe8"; // REPLACE WITH YOUR CONTRACT ADDRESS
        const DEX2Address = "0xD7ACd2a9FD159E69Bb102A1ca21C9a3e3A5F771B"; // REPLACE WITH YOUR CONTRACT ADDRESS
        const ArbitrageAddress = "0xa131AD247055FD2e2aA8b156A11bdEc81b9eAD95"; // REPLACE WITH YOUR CONTRACT ADDRESS

        if (!TokenAAddress || !web3.utils.isAddress(TokenAAddress)) {
            throw new Error("Please enter a valid TokenA contract address");
        }
        if (!TokenBAddress || !web3.utils.isAddress(TokenBAddress)) {
            throw new Error("Please enter a valid TokenB contract address");
        }
        if (!DEX1Address || !web3.utils.isAddress(DEX1Address)) {
            throw new Error("Please enter a valid DEX1 contract address");
        }
        if (!DEX2Address || !web3.utils.isAddress(DEX2Address)) {
            throw new Error("Please enter a valid DEX2 contract address");
        }
        if (!ArbitrageAddress || !web3.utils.isAddress(ArbitrageAddress)) {
            throw new Error("Please enter a valid Arbitrage contract address");
        }

        // 4. Create contract instance
        const TokenAInstance = new web3.eth.Contract(tokenABI, TokenAAddress);
        console.log("Connected to TokenA contract at:", TokenAAddress);

        const TokenBInstance = new web3.eth.Contract(tokenABI, TokenBAddress);
        console.log("Connected to TokenB contract at:", TokenBAddress);

        const DEX1Instance = new web3.eth.Contract(dexABI, DEX1Address);
        console.log("Connected to DEX1 contract at:", DEX1Address);

        const DEX2Instance = new web3.eth.Contract(dexABI, DEX2Address);
        console.log("Connected to DEX2 contract at:", DEX2Address);

        const ArbitrageInstance = new web3.eth.Contract(arbitrageABI, ArbitrageAddress);
        console.log("Connected to Arbitrage contract at:", ArbitrageAddress);

        // 5. Get LP token address
        const LpToken1Address = await DEX1Instance.methods.lpToken().call();
        const LpToken1Instance = new web3.eth.Contract(lpABI, LpToken1Address);
        console.log("Connected to LPToken1 contract at:", LpToken1Address);

        const LpToken2Address = await DEX2Instance.methods.lpToken().call();
        const LpToken2Instance = new web3.eth.Contract(lpABI, LpToken2Address);
        console.log("Connected to LPToken2 contract at:", LpToken2Address);     
        
        if (trader != await ArbitrageInstance.methods.owner().call()){
            throw new Error("Trader (2nd account) should be the owner of the Arbitrage contract");
        }

        await initializeBalance(LpToken1Instance, LpToken2Instance, TokenAInstance, TokenBInstance, DEX1Instance, DEX2Instance, lp, trader, ...accounts);
        
        // Code to simulate Profitable Arbitrage

        await printTraderBalances(TokenAInstance, TokenBInstance, trader, "Before profitable arbitrage");
        try {
            await simulateProfitableArbitrage(
                TokenAInstance,
                TokenBInstance,
                DEX1Instance,
                DEX2Instance,
                ArbitrageInstance,
                lp,
                trader
            );
        } catch (error) {
            console.error("Error during profitable arbitrage simulation:", error.message);
        }
        await printTraderBalances(TokenAInstance, TokenBInstance, trader, "After profitable arbitrage");

        // -------------------------------------
        
        await initializeBalance(LpToken1Instance, LpToken2Instance, TokenAInstance, TokenBInstance, DEX1Instance, DEX2Instance, lp, trader, ...accounts);
        
        console.log("------------------------------------------------------------------------------")

        // Code to simulate Unprofitable Arbitrage

        await printTraderBalances(TokenAInstance, TokenBInstance, trader, "Before unprofitable arbitrage");
        try{
            await simulateUnprofitableArbitrage(
                TokenAInstance,
                TokenBInstance,
                DEX1Instance,
                DEX2Instance,
                ArbitrageInstance,
                lp,
                trader
            );
        } catch (error) {
            console.error("Error during unprofitable arbitrage simulation:", error.message);
        }
        await printTraderBalances(TokenAInstance, TokenBInstance, trader, "After unprofitable arbitrage");

        // -------------------------------------


        console.log("Arbitrage simulation completed.");
    }
    catch (error) {
        console.error("Error during arbitrage simulation:", error.message);
    }
}


simulateArbitrage();