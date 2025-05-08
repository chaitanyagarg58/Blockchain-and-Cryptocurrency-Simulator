// Helper function to generate random integer between min and max (inclusive)
const fs = require("fs");

const outputFile = "metrics.csv";
const log_data = [["Action", "TVL", "Reserve Ratio", "Swap Volume of A", "Swap Volume of B", "Fees collected for A", "Fees collected for B", "Spot Price", "Slippage", "Trade Lot Fraction", "LP1", "LP2", "LP3", "LP4", "LP5"]];



function getRandomInt(min, max) {
    if (min > max) {
        return 0;
    }
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

async function distributeAndGetBalances(tokenInstance, ...addresses) {
    const balances = {};
    const totalSupply = await tokenInstance.methods.totalSupply().call();
    const share = web3.utils.toBN(totalSupply).div(web3.utils.toBN(addresses.length));

    for (const addr of addresses) {
        const balance = await tokenInstance.methods.balanceOf(addr).call();
        if (web3.utils.toBN(balance).gt(web3.utils.toBN(0))) {
            await tokenInstance.methods.transfer(addresses[0], web3.utils.toBN(balance).toString()).send({ from: addr });
        }
    }

    // Transfer to others (skip sourceAddress)
    for (const addr of addresses) {
        if (addr !== addresses[0]) {
            await tokenInstance.methods.transfer(addr, share.toString()).send({ from: addresses[0] });
        }
    }

    // Recompute balances
    for (const addr of addresses) {
        const balance = await tokenInstance.methods.balanceOf(addr).call();
        balances[addr] = balance;
    }

    return balances;
};

async function initializeBalance(LpTokenInstance, DEXInstance, TokenAInstance, TokenBInstance, LPs, traders) {
    for (const lp of LPs) {
        const lpTokenBalance = await LpTokenInstance.methods.balanceOf(lp).call();
        if (lpTokenBalance > 0) {
            await DEXInstance.methods.removeLiquidity(lpTokenBalance).send({ from: lp });
        }
    }

    balanceA = await distributeAndGetBalances(TokenAInstance, ...LPs, ...traders);
    console.log("TokenA Balances:", balanceA);
    balanceB = await distributeAndGetBalances(TokenBInstance, ...LPs, ...traders);
    console.log("TokenB Balances:", balanceB);
}

async function simulateDeposit(lp, TokenAInstance, TokenBInstance, DEXInstance) {
    const reserves = await DEXInstance.methods.spotPrice().call();
    const reserveA = reserves[0];
    const reserveB = reserves[1];

    let amountA, amountB;

    const lp_tokenA = await TokenAInstance.methods.balanceOf(lp).call();
    const lp_tokenB = await TokenBInstance.methods.balanceOf(lp).call();

    if (reserveA == 0 || reserveB == 0) {
        amountA = getRandomInt(1, lp_tokenA / 1e6) * 1e6; // Random amount of TokenA to deposit
        amountB = getRandomInt(1, lp_tokenB / 1e6) * 1e6; // Random amount of TokenB to deposit   
    }
    else {
        // Calculate the amount of TokenB needed to maintain the ratio
        const ratio = reserveA / reserveB;
        
        if (lp_tokenA > lp_tokenB * ratio) {
            amountB = getRandomInt(1, lp_tokenB / 1e6) * 1e6; // Random amount of TokenB to deposit
            amountA = Math.floor(amountB * ratio);
        }
        else {
            amountA = getRandomInt(1, lp_tokenA / 1e6) * 1e6; // Random amount of TokenA to deposit
            amountB = Math.floor(amountA / ratio);
        }
    }
    if (amountA == 0 || amountB == 0) return;
    if (amountA > lp_tokenA || amountB > lp_tokenB) return;
    // Approve the DEX contract to spend tokens on behalf of the LP
    await TokenAInstance.methods.approve(DEXInstance.options.address, amountA).send({ from: lp });
    await TokenBInstance.methods.approve(DEXInstance.options.address, amountB).send({ from: lp });
    // Add liquidity to the DEX
    await DEXInstance.methods.addLiquidity(amountA, amountB).send({ from: lp });
}

async function simulateWithdrawal(lp, LpTokenInstance, DEXInstance) {
    const lpTokenBalance = await LpTokenInstance.methods.balanceOf(lp).call();
    if (lpTokenBalance == 0) return;
    const amountLP = getRandomInt(1, lpTokenBalance / 1e6) * 1e6; // Random amount of LP tokens to withdraw
    if (amountLP == 0) return;
    if (amountLP > lpTokenBalance) return;
    // Withdraw liquidity from DEX
    await DEXInstance.methods.removeLiquidity(amountLP).send({ from: lp });
}

async function simulateSwap(trader, inputToken, outputToken, DEXInstance) {
    const inputTokenBalance = await inputToken.methods.balanceOf(trader).call();
    const inputTokenReserve = await DEXInstance.methods.getReserve(inputToken.options.address).call();
    const outputTokenReserve = await DEXInstance.methods.getReserve(outputToken.options.address).call();
    if (inputTokenBalance == 0 ||  inputTokenReserve == 0 || outputTokenReserve == 0) return;
    
    const min_val = Math.min(inputTokenBalance, 0.1 * inputTokenReserve);
    const inputAmount = getRandomInt(0, min_val / 1e6) * 1e6; // Random input amount for swap (up to 10)
    
    if (inputAmount == 0) return;

    // Approve DEX contract to spend input tokens
    await inputToken.methods.approve(DEXInstance.options.address, inputAmount).send({ from: trader });

    // Swap tokens
    await DEXInstance.methods.swap(inputToken.options.address, outputToken.options.address, inputAmount).send({ from: trader });
}

async function getLpBalances(lpList, LpTokenInstance) {
    // Use Promise.all to execute all calls concurrently
    const balances = [];
    for (const lp of lpList) {
        const balance = await LpTokenInstance.methods.balanceOf(lp).call();
        balances.push(balance); // Store the result in an array
    }

    return balances; // Return the list of balances
}

async function trackMetrics(action, LPs, LpTokenInstance, DEXInstance, diff_A, diff_B, reservesA_before_swap, reservesB_before_swap) {
    const totalSupplyLP = await LpTokenInstance.methods.totalSupply().call();
    const reserves = await DEXInstance.methods.spotPrice().call();
    const reserveA = reserves[0];
    const reserveB = reserves[1];

    const tvl = (2 * reserveA); // TVL in terms of TokenA
    const reserveRatio = reserveA / reserveB; // TokenA/TokenB ratio in pool
    const spotPrice = reserveA / reserveB; // Spot price (TokenA/TokenB)

    const lp_tokens_holdings = await getLpBalances(LPs, LpTokenInstance); // Store the result in a variable

    const swap_vols = await DEXInstance.methods.get_swaps_vol().call();
    const swaps_A = swap_vols[0];
    const swaps_B = swap_vols[1];

    const total_fees = await DEXInstance.methods.get_total_fees().call();
    const fees_A = total_fees[0];
    const fees_B = total_fees[1];

    // For slippage calculation:
    const slippage = {val : 0};
    const trade_lot_fraction = {val : 0};

    if(diff_A > 0 && reservesA_before_swap != 0 && reservesB_before_swap != 0 && diff_B != 0){
        const expected_price = reservesA_before_swap / reservesB_before_swap;
        const actual_price = -(diff_A / diff_B);
        slippage.val = ((actual_price - expected_price) * 100) / expected_price;

        trade_lot_fraction.val = (-diff_B) / reservesB_before_swap;
    }
    else if(diff_A < 0 && reservesA_before_swap != 0 && reservesB_before_swap != 0 && diff_A != 0){
        const expected_price = reservesB_before_swap / reservesA_before_swap;
        const actual_price = -(diff_B / diff_A);
        slippage.val = ((actual_price - expected_price) * 100) / expected_price;

        trade_lot_fraction.val = (-diff_A) / reservesA_before_swap;
    }

    console.log(`TVL: ${tvl} TokenA`);
    console.log(`Reserve Ratio: ${reserveRatio}`);
    console.log(`Spot Price: ${spotPrice}`);
    console.log("LP Token distribution: ", lp_tokens_holdings);

    console.log("Swap volume of A : ", swaps_A);
    console.log("Swap volume of B : ", swaps_B);

    console.log("Fees collected for A : ", fees_A);
    console.log("Fees collected for B : ", fees_B);

    console.log("Slippage : ", slippage.val);
    console.log("Trade Lot Fraction : ", trade_lot_fraction.val);

    log_data.push([action, tvl, reserveRatio, swaps_A, swaps_B, fees_A, fees_B, spotPrice, slippage.val, trade_lot_fraction.val, ...lp_tokens_holdings]);
}


async function simulateDEX() {
    try {
        console.log("Starting DEX contract interaction...");
        
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

        // 2. Get accounts
        const accounts = await web3.eth.getAccounts();

        const LPs = accounts.slice(0, 5); // First 5 users are LPs
        const traders = accounts.slice(5, 13); // Next 8 users are traders

        console.log("LPs:", LPs);
        console.log("Traders:", traders);

        // 3. Enter the address of your deployed Ballot contract
        const TokenAAddress = "0xbF7324BCFBc647960bf102Ba378B33CA0c8a3233"; // REPLACE WITH YOUR CONTRACT ADDRESS
        const TokenBAddress = "0xEae16F2ACfccc6d61F011c45C0e7CD998A027343"; // REPLACE WITH YOUR CONTRACT ADDRESS
        const DEXAddress = "0xFb3C40a2F3a57a7DB3D8Cfa050a0fDa7Aed8399F"; // REPLACE WITH YOUR CONTRACT ADDRESS

        if (!TokenAAddress || !web3.utils.isAddress(TokenAAddress)) {
            throw new Error("Please enter a valid TokenA contract address");
        }
        if (!TokenBAddress || !web3.utils.isAddress(TokenBAddress)) {
            throw new Error("Please enter a valid TokenB contract address");
        }
        if (!DEXAddress || !web3.utils.isAddress(DEXAddress)) {
            throw new Error("Please enter a valid DEX contract address");
        }
        
        // 4. Create contract instance
        const TokenAInstance = new web3.eth.Contract(tokenABI, TokenAAddress);
        console.log("Connected to TokenA contract at:", TokenAAddress);

        const TokenBInstance = new web3.eth.Contract(tokenABI, TokenBAddress);
        console.log("Connected to TokenB contract at:", TokenBAddress);

        const DEXInstance = new web3.eth.Contract(dexABI, DEXAddress);
        console.log("Connected to DEX contract at:", DEXAddress);

        // 5. Get LP token address
        const LpTokenAddress = await DEXInstance.methods.lpToken().call();
        const LpTokenInstance = new web3.eth.Contract(lpABI, LpTokenAddress);
        console.log("Connected to LPToken contract at:", LpTokenAddress);


        // 6. Initialize Token Distribution
        await initializeBalance(LpTokenInstance, DEXInstance, TokenAInstance, TokenBInstance, LPs, traders)

        // 7. Random Transaction Simulation
        const N = 100;  // Number of random transactions to simulate

        
        for (let i = 0; i < N; i++) {
            const action = getRandomInt(0, 2); // 0: Deposit, 1: Withdraw, 2: Swap
            
            // for slippage calculation: 
            const diff = {A : 0, B: 0};

            const reserves_before_swap = await DEXInstance.methods.spotPrice().call();
            const reservesA_before_swap = reserves_before_swap[0];
            const reservesB_before_swap = reserves_before_swap[1];

            console.log(`Iteration: ${i + 1}/${N}. Action: ${action}.`);

            if (action == 0) {
                await simulateDeposit(LPs[getRandomInt(0, LPs.length - 1)], TokenAInstance, TokenBInstance, DEXInstance);
            }
            else if (action == 1) {
                await simulateWithdrawal(LPs[getRandomInt(0, LPs.length - 1)], LpTokenInstance, DEXInstance);
            }
            else {
                const trader_idx = getRandomInt(0, traders.length -1);
                const init_A = await TokenAInstance.methods.balanceOf(traders[trader_idx]).call();
                const init_B = await TokenBInstance.methods.balanceOf(traders[trader_idx]).call();
                const dir = getRandomInt(0, 1);

                if (dir == 0) {
                    await simulateSwap(traders[trader_idx], TokenAInstance, TokenBInstance, DEXInstance);
                }
                else {
                    await simulateSwap(traders[trader_idx], TokenBInstance, TokenAInstance, DEXInstance);
                }

                const final_A = await TokenAInstance.methods.balanceOf(traders[trader_idx]).call();
                const final_B = await TokenBInstance.methods.balanceOf(traders[trader_idx]).call();

                diff.A = final_A - init_A;
                diff.B = final_B - init_B;
            }

            console.log(`Iteration Successfull`);
            await trackMetrics(action, LPs, LpTokenInstance, DEXInstance, diff.A, diff.B, reservesA_before_swap, reservesB_before_swap);
        }

        console.log("DEX contract simulation completed.");

        const csv_log = log_data.map(row => row.join(",")).join("\n");
        console.log("----------------------------------------------------------")
        console.log(csv_log);
    }
    catch (error) {
        console.error("Error during DEX simulation:", error);
    }
}

// Run the interaction
simulateDEX();